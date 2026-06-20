"""Overlay window — the always-on-top, click-through map layer (Qt).

Verbatim move of the Overlay class from the single-file build. Imports are
rewired to the new package. To keep the class body byte-for-byte identical,
this module re-exposes the names the class used as module-level globals
(DATA_PATH/STYLE_PATH/CONFIG_PATH/META_PATH and thin wrappers for the
config/meta helpers that now take explicit paths).
"""

import json
import math
import os
import threading
import time
import traceback
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets

from .constants import (
    APP_TITLE, CONFIG_VERSION, MAPS,
    DATA_URL, STYLE_URL,
    DEFAULT_HIDDEN_POSSIBLE_XP,
    VK_TAB, VK_CONTROL, VK_MENU, VK_SHIFT,
)
from .i18n import category_label, map_display, action_labels, tr
from . import i18n as _i18n
from .geometry import (
    detect_aspect_label, overlay_radius_from_spec, rotate90cw_norm,
    norm_to_grid, grid_distance, grid_to_meters, default_rect_ratio_by_aspect,
)
from .mapdata import (
    detect_data_format, get_map_block, get_category_list, find_style_by_category,
)
from .paths import load_json, save_json, udir
from .config import (
    build_default_config, default_keybinds, vk_to_label,
    load_or_replace_config as _load_or_replace_config,
)
from . import data_source as _ds
from . import images as _images
from .qt_adapters import q2rgb, rgb2q, qcolor_from_any, screenWH
from .win32 import key, topmost, click_through, set_mouse_transparent
from .runtime import ICON, CONFIG_PATH, META_PATH, USER_POIS_PATH, IMG_CACHE_DIR, data_path, style_path
from .widgets.panel import Panel
from .widgets.dialogs import KeyCaptureDialog
from .widgets.poi_editor import PoiEditorDialog
from . import user_data

# Resolve the user data files once at import (startup), matching the original
# module-level behavior. ensure_user_file copies bundled defaults if needed.
DATA_PATH = data_path()
STYLE_PATH = style_path()


# Thin wrappers preserving the original no-arg call sites in the class body.
def load_or_replace_config():
    return _load_or_replace_config(CONFIG_PATH)


def load_update_meta():
    return _ds.load_update_meta(META_PATH)


def save_update_meta(meta):
    return _ds.save_update_meta(META_PATH, meta)


def needs_data_update():
    return _ds.needs_data_update(META_PATH)


def fetch_remote_file(url, dst):
    return _ds.fetch_remote_file(url, dst)


def format_last_update(ts):
    """Compose the localized last-update label from the core status code."""
    status, when = _ds.last_update_status(ts)
    if status == "updated":
        return tr("Data updated: ") + when
    if status == "unknown":
        return tr("Data: unknown")
    return tr("Data: never updated")


class Overlay(QtWidgets.QWidget):
    dataUpdateFinished = QtCore.Signal(str)  # emits timestamp string
    dataUpdateProgress = QtCore.Signal(str)  # emits a status/progress message
    imageDownloadStarted = QtCore.Signal(str)
    imageDownloadFinished = QtCore.Signal(str, bool)  # url, success
    imagePrefetchFinished = QtCore.Signal(object)
    imageReady = QtCore.Signal()             # an on-demand image finished downloading

    def __init__(self):
        super().__init__(None, QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setMouseTracking(False)
        self._set_overlay_to_primary_monitor()


        if ICON:
            QtWidgets.QApplication.instance().setWindowIcon(QtGui.QIcon(ICON))
            self.setWindowIcon(QtGui.QIcon(ICON))

        if not os.path.isfile(DATA_PATH):
            raise RuntimeError(f"{tr('Missing data.json')}：{udir()}")
        if not os.path.isfile(STYLE_PATH):
            raise RuntimeError(f"{tr('Missing poiData.json')}：{udir()}")

        self.game_data = load_json(DATA_PATH)
        self.fmt = detect_data_format(self.game_data)
        if self.fmt == "unknown":
            raise RuntimeError(tr("Unrecognized data.json format"))

        self.poi_style = load_json(STYLE_PATH)

        # User-authored POIs (separate file, never overwritten by updates).
        self.user_pois = user_data.load_user_pois(USER_POIS_PATH)

        # Order of types controls draw order and GUI ordering.
        self.type_order = [
            "possible_xp",
            "spawns",
            "armories",
            "towers",
            "big_towers",
            "workbenches",
            "wild_targets",
            "brutes",
            "beetles",
            "easter_eggs",
            "melee_weapons",
            "cash_registers",
        ]

        self.type_specs = self._build_type_specs()

        W, H = screenWH()
        self.aspect = detect_aspect_label(W, H)

        self.data = load_or_replace_config()
        self._load_state_from_config(self.data)

        # Build the panel window.
        binds_label_map = action_labels()
        binds_current = {a: self._bind_label(a) for a in binds_label_map}
        self.panel = Panel(self.type_order, self.type_specs, self.global_scale, binds_label_map, binds_current, self.aspect, CONFIG_VERSION, self.minimize_to_tray, self.hold_tab_mode, self.block_shift_tab, self.panel_follow_tab)
        if ICON:
            self.panel.setWindowIcon(QtGui.QIcon(ICON))

        # Wire GUI events.
        self.panel.tnums.connect(self._set_num_switch)
        self.panel.mapSel.connect(self.switch)
        self.panel.resetColors.connect(self._reset_colors)
        self.panel.typeToggled.connect(self._type_toggle)
        self.panel.typeColor.connect(self._type_color)
        self.panel.scaleChanged.connect(self._scale_changed)
        self.panel.requestBindEdit.connect(self._edit_keybind)
        self.panel.resetConfig.connect(self._reset_config_to_defaults)
        self.panel.minimizeToTrayChanged.connect(self._set_minimize_to_tray)
        self.panel.holdTabModeChanged.connect(self._set_hold_tab_mode)
        self.panel.blockShiftTabChanged.connect(self._set_block_shift_tab)
        self.panel.panelFollowTabChanged.connect(self._set_panel_follow_tab)
        self.panel.forceRefresh.connect(self._force_data_refresh)
        self.panel.languageChanged.connect(self._set_language)
        self.panel.requestPoiEditor.connect(self._start_poi_pick_mode)
        self.panel.requestRuler.connect(self._enter_ruler_mode)
        self.panel.requestClearRulers.connect(self._clear_rulers)
        self.panel.requestOpenDataDir.connect(self._open_data_dir)

        # Seed GUI with current state.
        self.panel.chk_nums.setChecked(self.num_sw)
        self.panel.setMap(self.prof)
        for k in self.type_order:
            self.panel.setTypeState(k, self.types[k]["enabled"], rgb2q(self.types[k]["color"], self.type_specs[k]["default_fill"]))

        self._position_panel_top_right()

        # System tray setup.
        self.tray = None
        if self.minimize_to_tray:
            self._ensure_tray()

        # Make overlay click through and topmost on primary monitor.
        click_through(int(self.winId()))
        if self.visible and self.master:

            self._show_overlay_on_primary()

        else:

            self.hide()
        topmost(int(self.winId()))

        # Edge detection for hotkeys so they do not toggle repeatedly while held.
        self.p_toggle_master = False
        self.p_hide = False
        self.p_toggle_overlay = False
        self.p_hide_hovered = False

        # Hover state is computed each tick when visible.
        self.hover = None
        # Hover needs to be forgiving: the overlay reads the system cursor, not
        # the game reticle, so a tiny hit box makes image previews feel dead.
        self.hover_radius = 18
        # Last hovered point identity, to repaint only when it changes.
        self._last_hover_id = None

        # POI pick mode: when active, the overlay captures the mouse (click-
        # through is temporarily disabled) and the next click yields a grid
        # coordinate. _pick_pos is the current cursor position for the crosshair.
        self._pick_mode = False
        self._pick_pos = None
        self._pick_map = ""
        self._pick_cat = ""

        # Ruler mode: measure the distance between two clicked points. _ruler_a
        # is the fixed first point (grid coords); _ruler_pos is the live cursor.
        self._ruler_mode = False
        self._ruler_a = None
        self._ruler_pos = None
        self._ruler_hover_delete = None
        self._rulers = []
        self._ruler_endpoint_radius = 14

        # Decoded hover-preview pixmaps, memoized by cache path (path -> QPixmap
        # or None). Avoids re-reading the disk every paint frame.
        self._hover_pm_cache = {}
        # URLs currently being downloaded on demand (de-dupe repeated hovers).
        self._img_inflight = set()
        # url -> "loading" | "ready" | "failed"; used for visible feedback.
        self._img_status = {}
        self._img_failed_at = {}
        self._img_prefetch_queued = set()
        self._image_prefetch_running = False
        self._image_prefetch_pending = False

        # Cache computed point lists per map to avoid rebuilding every frame.
        self.cache = {}
        self._rebuild_all_caches()

        # Save once at the end to ensure config contains any missing keys we added.
        self._save()
        
        # Start with the control panel minimized to tray.
        if self.minimize_to_tray:
            self._hide_panel_to_tray()
        elif self.panel_follow_tab and not self.visible:
            # Follow-Tab on and overlay starts hidden: keep the panel hidden
            # too; it appears when the overlay is shown via Tab.
            self.panel.hide()
        else:
            self.panel.show()
            self._position_panel_top_right()
        # Timer tick drives input polling and hover updates.
        self.t = QtCore.QTimer(self)
        self.t.timeout.connect(self._tick_safe)
        self.t.start(16)

        # Minimize to tray needs access to the panel state changes.
        self.panel.installEventFilter(self)

        # Wire data update signal and seed the label with last known timestamp.
        self.dataUpdateFinished.connect(self._on_data_update_finished)
        self.dataUpdateProgress.connect(self.panel.setLastUpdateText)
        self.imageDownloadStarted.connect(self._on_image_download_started)
        self.imageDownloadFinished.connect(self._on_image_download_finished)
        self.imagePrefetchFinished.connect(self._on_image_prefetch_finished)
        self.imageReady.connect(self.update)
        self.panel.setLastUpdateText(format_last_update(load_update_meta().get("last_check", "")))
        self._start_update_check()
        self._start_image_prefetch(self.game_data)

    def eventFilter(self, obj, ev):
        if obj is self.panel:
            if ev.type() == QtCore.QEvent.WindowStateChange:
                if self.minimize_to_tray and self.panel.isMinimized():
                    self._hide_panel_to_tray()
                    return True
        return super().eventFilter(obj, ev)

    def _ensure_tray(self):
        """
        Creates tray icon and menu once.
        Tray is only used when minimize_to_tray is enabled, but we keep it available.
        """
        if self.tray is not None:
            return

        self.tray = QtWidgets.QSystemTrayIcon(self)
        if ICON:
            self.tray.setIcon(QtGui.QIcon(ICON))
        else:
            self.tray.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))

        menu = QtWidgets.QMenu()
        act_restore = QtGui.QAction(tr("Restore control panel"), menu)
        act_quit = QtGui.QAction(tr("Quit"), menu)
        menu.addAction(act_restore)
        menu.addSeparator()
        menu.addAction(act_quit)

        act_restore.triggered.connect(self._restore_panel_from_tray)
        act_quit.triggered.connect(QtWidgets.QApplication.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self._restore_panel_from_tray()

    def _hide_panel_to_tray(self):
        self._ensure_tray()
        self.panel.hide()
        self.panel.setWindowState(QtCore.Qt.WindowNoState)
        try:
            self.tray.showMessage(APP_TITLE, tr("Control panel minimized to tray"), QtWidgets.QSystemTrayIcon.Information, 1500)
        except:
            pass

    def _restore_panel_from_tray(self):
        self.panel.showNormal()
        self._position_panel_top_right()
        self.panel.raise_()
        self.panel.activateWindow()

    def _set_minimize_to_tray(self, v: bool):
        self.minimize_to_tray = bool(v)
        self._save()
    def _set_hold_tab_mode(self, v: bool):
        self.hold_tab_mode = bool(v)
        self._save()

    def _set_panel_follow_tab(self, v: bool):
        self.panel_follow_tab = bool(v)
        # Apply immediately: if turning follow off, make sure the panel is
        # reachable again; if on, sync it to the current overlay visibility.
        if self.panel_follow_tab:
            self._sync_panel_visibility()
        elif not self.minimize_to_tray:
            self.panel.show()
            self._position_panel_top_right()
        self._save()

    def _sync_panel_visibility(self):
        """When follow-Tab is on, the panel shows/hides with the overlay.

        Skipped while minimized to tray (the tray owns panel visibility) and
        when follow-Tab is off (panel stays put)."""
        if not self.panel_follow_tab or self.minimize_to_tray:
            return
        if self.visible:
            self.panel.show()
            self._position_panel_top_right()
        else:
            self.panel.hide()

    def _set_block_shift_tab(self, v: bool):
        self.block_shift_tab = bool(v)
        self._save()

    def _set_language(self, code: str):
        """Persist the chosen language. Takes effect on next launch (the UI is
        built once at startup); show a restart hint in the panel."""
        self.language = str(code)
        self._save()
        try:
            self.panel.lbl_lang_hint.setVisible(True)
        except Exception:
            pass

    def _open_poi_editor(self, init_map: str = "", init_cat: str = "", prefill_xy=None):
        """Open the user-POI editor; on close, persist and hot-refresh.

        The dialog edits a working copy, so this only commits when it returns.
        User points go to user_pois.json; data.json is never touched.
        """
        dlg = PoiEditorDialog(self.user_pois, ICON, self.panel,
                              init_map=init_map, init_cat=init_cat,
                              prefill_xy=prefill_xy)
        dlg.exec()
        self.user_pois = dlg.result_pois
        user_data.save_user_pois(USER_POIS_PATH, self.user_pois)
        self._rebuild_all_caches()
        self.update()

        # If the user asked to pick a coordinate from the map, enter pick mode;
        # the picked coordinate reopens the editor with it prefilled.
        if dlg.pick_requested:
            self._enter_pick_mode(dlg.pick_map, dlg.pick_cat)

    def _start_poi_pick_mode(self, category: str = ""):
        """Enter continuous direct-pick mode for user POIs."""
        cat = str(category or "")
        if cat not in self.type_order or cat == "possible_xp":
            cat = next((t for t in self.type_order if t != "possible_xp"), "")
        if not cat:
            return
        self._enter_pick_mode(self.prof, cat)

    # ── POI pick mode ─────────────────────────────────────────────────────
    def _enter_pick_mode(self, pick_map: str, pick_cat: str):
        """Switch the overlay to the target map and capture the mouse so the
        next click yields a grid coordinate. Click-through is disabled here
        and restored in _exit_pick_mode."""
        self._pick_map = pick_map
        self._pick_cat = pick_cat
        # Show the map being edited so its official points serve as reference.
        if pick_map in MAPS and pick_map != self.prof:
            self.switch(pick_map)
        self.master = True
        self.visible = True
        self._show_overlay_on_primary()
        self._pick_mode = True
        self._pick_pos = None
        self.setMouseTracking(True)
        set_mouse_transparent(int(self.winId()), False)  # capture the mouse
        self.update()
        self._poll_tool_cursor()

    def _exit_pick_mode(self):
        self._pick_mode = False
        self._pick_pos = None
        self.setMouseTracking(False)
        set_mouse_transparent(int(self.winId()), True)  # restore pass-through
        self.update()

    def _open_data_dir(self):
        """Open the app data folder (%LOCALAPPDATA%\\HuntOverlay) in the file
        manager via Qt's cross-platform handler."""
        try:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(udir()))
        except Exception:
            pass

    # ── Ruler mode ────────────────────────────────────────────────────────
    def _enter_ruler_mode(self):
        """Capture the mouse to measure the distance between two clicks."""
        self.master = True
        self.visible = True
        self._show_overlay_on_primary()
        self._ruler_mode = True
        self._ruler_a = None
        self._ruler_pos = None
        self.setMouseTracking(True)
        set_mouse_transparent(int(self.winId()), False)
        self.update()
        self._poll_tool_cursor()

    def _exit_ruler_mode(self):
        self._ruler_mode = False
        self._ruler_a = None
        self._ruler_pos = None
        self.setMouseTracking(False)
        set_mouse_transparent(int(self.winId()), True)
        self.update()

    def mouseMoveEvent(self, e):
        if self._pick_mode:
            self._set_pick_pos(e.position())
        elif self._ruler_mode:
            self._set_ruler_pos(e.position())
        else:
            super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        if self._ruler_mode:
            if e.button() == QtCore.Qt.LeftButton and self.rect:
                self._ruler_pos = e.position()
                if self._ruler_hover_delete is not None:
                    self._delete_hovered_ruler()
                    return

                old_dirty = self._ruler_dirty_region(self._ruler_pos)
                gx, gy = self._screen_to_grid(e.position())
                if self._ruler_a is None:
                    self._ruler_a = (gx, gy)        # first click: anchor
                else:
                    self._rulers.append({"map": self.prof, "a": self._ruler_a, "b": (gx, gy)})
                    self._ruler_a = None            # completed; next click starts another ruler
                self._update_region(old_dirty.united(self._ruler_dirty_region(self._ruler_pos)))
            else:
                self._exit_ruler_mode()             # right-click exits
            return
        if not self._pick_mode:
            super().mousePressEvent(e)
            return
        if e.button() == QtCore.Qt.LeftButton and self.rect:
            x, y = self._screen_to_grid(e.position())
            mp, cat = self._pick_map, self._pick_cat
            try:
                self.user_pois = user_data.add_point(self.user_pois, mp, cat, x, y)
                user_data.save_user_pois(USER_POIS_PATH, self.user_pois)
                self._rebuild_all_caches()
                self.update()
            except ValueError:
                pass
        else:
            # Right-click / other: cancel continuous pick mode.
            self._exit_pick_mode()

    def keyPressEvent(self, e):
        if self._pick_mode and e.key() == QtCore.Qt.Key_Escape:
            self._exit_pick_mode()
        elif self._ruler_mode and e.key() == QtCore.Qt.Key_Escape:
            self._exit_ruler_mode()
        else:
            super().keyPressEvent(e)

    def _update_region(self, region: QtGui.QRegion):
        """Immediately repaint a bounded tool region.

        Tool overlays track the cursor; queued update() calls can visibly lag
        on translucent top-level Windows windows.
        """
        if region is None or region.isEmpty():
            self.repaint()
            return
        self.repaint(region)

    def _tool_cursor_pos(self):
        return QtCore.QPointF(self.mapFromGlobal(QtGui.QCursor.pos()))

    def _set_pick_pos(self, pos) -> bool:
        old_pos = self._pick_pos
        if self._same_pixel(old_pos, pos):
            return False
        self._pick_pos = QtCore.QPointF(pos)
        self._update_pick_region(old_pos, self._pick_pos)
        return True

    def _set_ruler_pos(self, pos) -> bool:
        old_pos = self._ruler_pos
        if self._same_pixel(old_pos, pos):
            return False
        old_dirty = self._ruler_dirty_region(old_pos).united(self._ruler_delete_dirty_region(self._ruler_hover_delete))
        self._ruler_pos = QtCore.QPointF(pos)
        self._ruler_hover_delete = self._hit_ruler_endpoint(self._ruler_pos)
        new_dirty = self._ruler_dirty_region(self._ruler_pos).united(self._ruler_delete_dirty_region(self._ruler_hover_delete))
        self._update_region(old_dirty.united(new_dirty))
        return True

    def _poll_tool_cursor(self):
        if not self.visible:
            return
        pos = self._tool_cursor_pos()
        if self._pick_mode:
            self._set_pick_pos(pos)
        elif self._ruler_mode:
            self._set_ruler_pos(pos)

    def _same_pixel(self, a, b) -> bool:
        if a is None or b is None:
            return False
        return int(a.x()) == int(b.x()) and int(a.y()) == int(b.y())

    def _tool_bounds(self) -> QtCore.QRect:
        return QtCore.QRect(0, 0, max(1, self.width()), max(1, self.height()))

    def _bounded_region(self, region: QtGui.QRegion) -> QtGui.QRegion:
        return region.intersected(QtGui.QRegion(self._tool_bounds()))

    def _point_dirty_region(self, pos, label_width: int = 220, label_height: int = 76) -> QtGui.QRegion:
        if pos is None:
            return QtGui.QRegion()
        x, y = int(pos.x()), int(pos.y())
        region = QtGui.QRegion(QtCore.QRect(x - 24, y - 24, 48, 48))
        region = region.united(QtGui.QRegion(QtCore.QRect(x + 8, y + 8, label_width, label_height)))
        return region

    def _pick_dirty_region(self, pos) -> QtGui.QRegion:
        """Region affected by the pick crosshair, cursor dot, and coord label."""
        if pos is None or not self.rect:
            return QtGui.QRegion()
        x, y = int(pos.x()), int(pos.y())
        region = self._point_dirty_region(pos)
        region = region.united(QtGui.QRegion(QtCore.QRect(self.rect.left(), y - 3, self.rect.width(), 7)))
        region = region.united(QtGui.QRegion(QtCore.QRect(x - 3, self.rect.top(), 7, self.rect.height())))
        return self._bounded_region(region)

    def _update_pick_region(self, old_pos, new_pos):
        dirty = self._pick_dirty_region(old_pos).united(self._pick_dirty_region(new_pos))
        self._update_region(dirty)

    def _line_dirty_region(self, ax: float, ay: float, bx: float, by: float, width: int = 18) -> QtGui.QRegion:
        dx = bx - ax
        dy = by - ay
        length = math.hypot(dx, dy)
        if length <= 0.5:
            return QtGui.QRegion(QtCore.QRect(int(ax) - width, int(ay) - width, width * 2, width * 2))

        half = width / 2.0
        nx = -dy / length * half
        ny = dx / length * half
        poly = QtGui.QPolygon([
            QtCore.QPoint(int(round(ax + nx)), int(round(ay + ny))),
            QtCore.QPoint(int(round(bx + nx)), int(round(by + ny))),
            QtCore.QPoint(int(round(bx - nx)), int(round(by - ny))),
            QtCore.QPoint(int(round(ax - nx)), int(round(ay - ny))),
        ])
        return QtGui.QRegion(poly)

    def _ruler_anchor_pos(self):
        if self._ruler_a is None or not self.rect:
            return None
        ax, ay = self._ruler_a
        return self._grid_to_screen_pos(ax, ay)

    def _grid_to_screen_pos(self, gx, gy):
        au, av = rotate90cw_norm(gx, gy)
        return QtCore.QPointF(
            self.rect.left() + au * self.rect.width(),
            self.rect.top() + av * self.rect.height(),
        )

    def _ruler_distance_text(self, a, b) -> str:
        ax, ay = a
        bx, by = b
        gdist = grid_distance(ax, ay, bx, by)
        meters = grid_to_meters(gdist)
        return f"≈ {meters:.0f} m  ({gdist:.0f} u)"

    def _iter_current_rulers(self):
        for idx, item in enumerate(self._rulers):
            if item.get("map") == self.prof:
                yield idx, item

    def _hit_ruler_endpoint(self, pos):
        if pos is None or not self.rect:
            return None
        px, py = float(pos.x()), float(pos.y())
        radius2 = float(self._ruler_endpoint_radius * self._ruler_endpoint_radius)
        for idx, item in self._iter_current_rulers():
            for endpoint in ("a", "b"):
                ep = item.get(endpoint)
                if not ep:
                    continue
                sp = self._grid_to_screen_pos(ep[0], ep[1])
                dx = px - sp.x()
                dy = py - sp.y()
                if dx * dx + dy * dy <= radius2:
                    return (idx, endpoint)
        return None

    def _ruler_delete_dirty_region(self, hit) -> QtGui.QRegion:
        if hit is None or not self.rect:
            return QtGui.QRegion()
        idx, endpoint = hit
        if not (0 <= idx < len(self._rulers)):
            return QtGui.QRegion()
        ep = self._rulers[idx].get(endpoint)
        if not ep:
            return QtGui.QRegion()
        sp = self._grid_to_screen_pos(ep[0], ep[1])
        x, y = int(sp.x()), int(sp.y())
        return self._bounded_region(QtGui.QRegion(QtCore.QRect(x - 20, y - 20, 40, 40)))

    def _delete_hovered_ruler(self):
        hit = self._ruler_hover_delete
        if hit is None:
            return
        dirty = self._ruler_delete_dirty_region(hit)
        idx, _endpoint = hit
        if 0 <= idx < len(self._rulers):
            item = self._rulers[idx]
            dirty = dirty.united(self._stored_ruler_dirty_region(item))
            del self._rulers[idx]
        self._ruler_hover_delete = None
        self._update_region(dirty)

    def _clear_rulers(self):
        if not self._rulers:
            return
        self._rulers = []
        self._ruler_hover_delete = None
        self.update()

    def _stored_ruler_dirty_region(self, item) -> QtGui.QRegion:
        if not item or not self.rect:
            return QtGui.QRegion()
        a = item.get("a")
        b = item.get("b")
        if not a or not b:
            return QtGui.QRegion()
        ap = self._grid_to_screen_pos(a[0], a[1])
        bp = self._grid_to_screen_pos(b[0], b[1])
        dirty = self._line_dirty_region(ap.x(), ap.y(), bp.x(), bp.y(), width=24)
        dirty = dirty.united(self._point_dirty_region(ap, label_width=0, label_height=0))
        dirty = dirty.united(self._point_dirty_region(bp, label_width=0, label_height=0))
        midx = int((ap.x() + bp.x()) / 2)
        midy = int((ap.y() + bp.y()) / 2)
        dirty = dirty.united(QtGui.QRegion(QtCore.QRect(midx - 90, midy - 28, 180, 56)))
        return self._bounded_region(dirty)

    def _ruler_dirty_region(self, pos) -> QtGui.QRegion:
        """Region affected by the ruler line, cursor dot, and label."""
        if pos is None:
            return QtGui.QRegion()

        dirty = self._point_dirty_region(pos, label_width=280, label_height=96)

        anchor_pos = self._ruler_anchor_pos()
        if anchor_pos is not None:
            dirty = dirty.united(self._point_dirty_region(anchor_pos, label_width=0, label_height=0))
            dirty = dirty.united(self._line_dirty_region(anchor_pos.x(), anchor_pos.y(), pos.x(), pos.y()))

        return self._bounded_region(dirty)

    def _screen_to_grid(self, pos):
        """Map a cursor position (overlay-local) inside self.rect back to a
        0-4095 grid coordinate via the inverse of the render transform."""
        u = (pos.x() - self.rect.left()) / max(1, self.rect.width())
        v = (pos.y() - self.rect.top()) / max(1, self.rect.height())
        return norm_to_grid(u, v)

    def _hover_pixmap(self, urls):
        """Return a scaled QPixmap for the first cached image in urls, or None.

        Startup/data refresh prefetches the full cache in the background.
        Hover still triggers a priority download for missing images so the
        user does not wait for the prefetch queue to reach this URL. Bad cache
        files are removed so a later hover can retry instead of being stuck.
        """
        if not urls:
            return None
        for url in urls:
            if not _images.is_allowed_image_url(url):
                self._img_status[url] = "failed"
                continue

            path = _images.cache_path(IMG_CACHE_DIR, url)
            if os.path.isfile(path):
                if not _images.cached_image_valid(path):
                    self._remove_bad_image_cache(path, url)
                    self._img_failed_at.pop(url, None)
                    self._img_status.pop(url, None)
                    self._request_image_download(url)
                    return None

                if path in self._hover_pm_cache:
                    return self._hover_pm_cache[path]

                pm = QtGui.QPixmap(path)
                if pm.isNull():
                    self._remove_bad_image_cache(path, url)
                    self._img_status[url] = "failed"
                    self._img_failed_at[url] = time.monotonic()
                    continue

                # Cap the preview size so it never dominates the screen.
                pm = pm.scaled(280, 280, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                self._hover_pm_cache[path] = pm
                self._img_status[url] = "ready"
                return pm

            self._request_image_download(url)
            return None

        return None

    def _remove_bad_image_cache(self, path: str, url: str):
        self._hover_pm_cache.pop(path, None)
        try:
            os.remove(path)
        except OSError:
            pass
        self._img_status[url] = "failed"
        self._img_failed_at[url] = time.monotonic()

    def _hover_image_message(self, urls):
        if not urls:
            return ""
        saw_failed = False
        for url in urls:
            state = self._img_status.get(url, "")
            if state == "loading":
                return tr("Loading image...")
            if state == "failed":
                saw_failed = True
        if saw_failed:
            return tr("Image unavailable")
        return ""



    def _force_data_refresh(self):
        self.panel.setLastUpdateText(tr("Data: updating..."))
        self.panel.btn_force_refresh.setEnabled(False)
        t = threading.Thread(target=self._run_data_update, daemon=True)
        t.start()

    def _start_update_check(self):
        if needs_data_update():
            self.panel.setLastUpdateText(tr("Data: updating..."))
            t = threading.Thread(target=self._run_data_update, daemon=True)
            t.start()

    def _run_data_update(self):
        """Runs in a background thread. Downloads both files then emits the finished signal."""
        self.dataUpdateProgress.emit(tr("Updating map data..."))
        ok_data  = fetch_remote_file(DATA_URL,  DATA_PATH)
        ok_style = fetch_remote_file(STYLE_URL, STYLE_PATH)
        ts = datetime.now().isoformat(timespec="seconds") if (ok_data or ok_style) else ""
        meta = load_update_meta()
        if ok_data or ok_style:
            meta["last_check"] = ts
            save_update_meta(meta)
        # Image cache prefetch happens in a separate throttled worker after
        # startup/data refresh. Sweep any stale .part leftovers first.
        try:
            _images.cleanup_partials(IMG_CACHE_DIR)
        except Exception:
            pass
        self.dataUpdateFinished.emit(ts)

    def _image_cache_missing(self, url: str) -> bool:
        path = _images.cache_path(IMG_CACHE_DIR, url)
        return not (os.path.isfile(path) and _images.cached_image_valid(path))

    def _start_image_prefetch(self, game_data=None):
        if self._image_prefetch_running:
            self._image_prefetch_pending = True
            return

        urls = _images.collect_image_urls(game_data if game_data is not None else self.game_data)
        missing = [url for url in urls if self._image_cache_missing(url)]
        if not missing:
            return

        self._image_prefetch_running = True
        self._img_prefetch_queued.update(missing)

        def worker(urls_to_fetch):
            try:
                os.makedirs(IMG_CACHE_DIR, exist_ok=True)
                for url in urls_to_fetch:
                    if not _images.is_allowed_image_url(url):
                        continue
                    if not self._image_cache_missing(url):
                        continue
                    if url in self._img_inflight:
                        continue

                    path = _images.cache_path(IMG_CACHE_DIR, url)
                    self.imageDownloadStarted.emit(url)
                    ok = _ds.fetch_image(url, path)
                    self.imageDownloadFinished.emit(url, ok)
            finally:
                self.imagePrefetchFinished.emit(urls_to_fetch)

        threading.Thread(target=worker, args=(list(missing),), daemon=True).start()

    def _request_image_download(self, url: str):
        """On-demand download of a single image (method B), off the UI thread.

        Triggered when hovering a point whose image is not cached yet. The
        background prefetch normally fills the cache, but hover is prioritized
        so a visible point is not blocked behind the full startup queue.
        De-duped via _img_inflight so repeated hovers do not queue the same
        URL twice; repaints when done so the image appears.
        """
        if not _images.is_allowed_image_url(url):
            self._img_status[url] = "failed"
            return
        path = _images.cache_path(IMG_CACHE_DIR, url)
        if os.path.isfile(path) and _images.cached_image_valid(path):
            self._img_status[url] = "ready"
            return
        if url in self._img_inflight:
            self._img_status[url] = "loading"
            return

        failed_at = self._img_failed_at.get(url, 0.0)
        if failed_at and time.monotonic() - failed_at < 30.0:
            return

        self._img_inflight.add(url)
        self._img_status[url] = "loading"
        self._img_prefetch_queued.discard(url)

        def worker():
            ok = False
            try:
                os.makedirs(IMG_CACHE_DIR, exist_ok=True)
                ok = _ds.fetch_image(url, path)
            except Exception:
                pass
            finally:
                self.imageDownloadFinished.emit(url, ok)

        threading.Thread(target=worker, daemon=True).start()

    def _on_image_download_started(self, url: str):
        self._img_prefetch_queued.discard(url)
        self._img_inflight.add(url)
        self._img_status[url] = "loading"

    def _finish_image_download(self, url: str, ok: bool):
        path = _images.cache_path(IMG_CACHE_DIR, url)
        if ok and os.path.isfile(path) and _images.cached_image_valid(path):
            self._img_status[url] = "ready"
            self._img_failed_at.pop(url, None)
        else:
            self._img_status[url] = "failed"
            self._img_failed_at[url] = time.monotonic()
        self._img_inflight.discard(url)
        self._img_prefetch_queued.discard(url)

    def _on_image_download_finished(self, url: str, ok: bool):
        """Slot — runs on the main thread after an image worker completes."""
        self._finish_image_download(url, ok)
        if self._hover_uses_image_url(url):
            self.imageReady.emit()

    def _hover_uses_image_url(self, url: str) -> bool:
        if self.hover is None:
            return False
        raw = self.hover.get("pt_ref", {}).get("raw", {})
        imgs = raw.get("u", []) if isinstance(raw, dict) else []
        return url in imgs

    def _on_image_prefetch_finished(self, urls):
        for url in urls or []:
            self._img_prefetch_queued.discard(url)
        self._image_prefetch_running = False
        if self._image_prefetch_pending:
            self._image_prefetch_pending = False
            self._start_image_prefetch(self.game_data)

    def _on_data_update_finished(self, ts: str):
        """Slot — runs on the main thread after the background download completes."""
        if ts:
            try:
                self.game_data = load_json(DATA_PATH)
                self.fmt = detect_data_format(self.game_data)
                self.poi_style = load_json(STYLE_PATH)
                self.type_specs = self._build_type_specs()
                self._rebuild_all_caches()
                self.update()
                self._start_image_prefetch(self.game_data)
            except Exception:
                pass
        self.panel.setLastUpdateText(format_last_update(ts if ts else load_update_meta().get("last_check", "")))
        self.panel.btn_force_refresh.setEnabled(True)

    def _build_type_specs(self):
        specs = {}

        # possible_xp is a special union category.
        specs["possible_xp"] = {
            "label": category_label("possible_xp", "Possible XP Location"),
            "border": QtGui.QColor("#FFFFFF"),
            "default_fill": QtGui.QColor("#FFD34D"),
            "radius_px": 6,
        }

        def add_from_style(category, fallback_label):
            spec = find_style_by_category(self.poi_style, category) or {}
            label = category_label(category, spec.get("label", fallback_label))
            border = qcolor_from_any(spec.get("borderColor", "#555555"), QtGui.QColor("#555555"))
            fill = qcolor_from_any(spec.get("fillColor", "#B4B4B4"), QtGui.QColor("#B4B4B4"))
            radius_px = overlay_radius_from_spec(spec.get("radius", 12))
            specs[category] = {"label": str(label), "border": border, "default_fill": fill, "radius_px": radius_px}

        add_from_style("spawns", "Spawns")
        add_from_style("armories", "Armories")
        add_from_style("towers", "Hunting Towers")
        add_from_style("big_towers", "Watch Towers")
        add_from_style("workbenches", "Workbenches")
        add_from_style("wild_targets", "Wild Targets")
        add_from_style("brutes", "Brutes")
        add_from_style("beetles", "Beetles")
        add_from_style("easter_eggs", "Easter Eggs")
        add_from_style("melee_weapons", "Melee Weapons")
        add_from_style("cash_registers", "Cash Registers")

        return specs

    def _normalize_keybinds(self, binds: dict) -> dict:
        """
        Merges config keybinds with defaults and forces correct types.
        Unknown keys are ignored.
        """
        base = default_keybinds()
        merged = {k: dict(v) for k, v in base.items()}

        if isinstance(binds, dict):
            for k, v in binds.items():
                if k not in merged:
                    continue
                if not isinstance(v, dict):
                    continue
                for kk, vv in v.items():
                    merged[k][kk] = vv

        for k, v in merged.items():
            try:
                v["vk"] = int(v.get("vk", base[k]["vk"]))
            except:
                v["vk"] = int(base[k]["vk"])

            if k == "hide_hovered":
                v["ctrl"] = bool(v.get("ctrl", True))
                v["alt"] = bool(v.get("alt", True))
                v["shift"] = bool(v.get("shift", True))

        return merged

    def _load_state_from_config(self, d: dict):
        """
        Loads stateful runtime fields from the config dict.
        This is used at startup and after a full reset to default config.
        """
        st = d.get("settings", {}) if isinstance(d, dict) else {}
        if not isinstance(st, dict):
            st = {}

        self.num_sw = bool(st.get("enable_num_switch", True))
        sel = st.get("selected_map", MAPS[0])
        self.prof = sel if sel in MAPS else MAPS[0]

        # Apply saved language before any UI is built so tr() uses it.
        self.language = st.get("language", _i18n.DEFAULT_LANG)
        _i18n.set_language(self.language)
        self.visible = bool(st.get("visible_overlay", False))
        self.master = bool(st.get("master_on", True))

        self.global_scale = float(st.get("global_scale", 1.00))
        if self.global_scale < 0.10: self.global_scale = 0.10
        if self.global_scale > 5.00: self.global_scale = 5.00

        self.minimize_to_tray = bool(st.get("minimize_to_tray", False))
        self.hold_tab_mode = bool(st.get("hold_tab_to_show", False))
        self.block_shift_tab = bool(st.get("block_shift_tab", True))
        # When True, the control panel shows/hides together with the overlay
        # (Tab). Default False = panel stays put so users can always reach it
        # without holding Tab.
        self.panel_follow_tab = bool(st.get("panel_follow_tab", False))


        self.binds = self._normalize_keybinds(st.get("keybinds", {}))

        # Per type settings.
        self.types = st.get("types", {})
        if not isinstance(self.types, dict):
            self.types = {}
        for k in self.type_order:
            if k not in self.types or not isinstance(self.types.get(k), dict):
                self.types[k] = {"enabled": True, "color": q2rgb(self.type_specs[k]["default_fill"])}
            if "enabled" not in self.types[k]:
                self.types[k]["enabled"] = True
            if "color" not in self.types[k]:
                self.types[k]["color"] = q2rgb(self.type_specs[k]["default_fill"])

        # Hidden lists.
        self.hidden = st.get("hidden", {})
        if not isinstance(self.hidden, dict):
            self.hidden = {}
        for k in self.type_order:
            if k not in self.hidden or not isinstance(self.hidden.get(k), list):
                self.hidden[k] = []

        # Ensure default hidden possible_xp entries exist.
        px = self.hidden.get("possible_xp", [])
        if not isinstance(px, list):
            px = []
        for s in DEFAULT_HIDDEN_POSSIBLE_XP:
            if s not in px:
                px.append(s)
        self.hidden["possible_xp"] = px

        self.hidden_sets = {k: set(self.hidden.get(k, [])) for k in self.type_order}

        # Apply aspect aware rect.
        self.rect = None
        self._apply_rect()

    def _bind_pressed(self, name: str) -> bool:
        b = self.binds.get(name, {})
        try:
            vk = int(b.get("vk", 0))
        except:
            return False
        if vk == 0:
            return False
        if vk == VK_TAB and (key(VK_CONTROL) or key(VK_MENU)):
            return False
        if vk == VK_TAB and self.block_shift_tab and key(VK_SHIFT):
            return False

        if name == "hide_hovered":
            need_ctrl = bool(b.get("ctrl", True))
            need_alt = bool(b.get("alt", True))
            need_shift = bool(b.get("shift", True))
            if need_ctrl and not key(VK_CONTROL): return False
            if need_alt and not key(VK_MENU): return False
            if need_shift and not key(VK_SHIFT): return False
            return key(vk)

        return key(vk)

    def _bind_label(self, name: str) -> str:
        b = self.binds.get(name, {})
        try:
            vk = int(b.get("vk", 0))
        except:
            vk = 0

        if name == "hide_hovered":
            parts = []
            if bool(b.get("ctrl", True)): parts.append("Ctrl")
            if bool(b.get("alt", True)): parts.append("Alt")
            if bool(b.get("shift", True)): parts.append("Shift")
            parts.append(vk_to_label(vk))
            return " + ".join(parts)

        return vk_to_label(vk)

    def _save(self):
        st = self.data.setdefault("settings", {})
        self.data["version"] = CONFIG_VERSION

        st["enable_num_switch"] = self.num_sw
        st["selected_map"] = self.prof
        st["visible_overlay"] = self.visible
        st["master_on"] = self.master
        st["global_scale"] = float(self.global_scale)
        st["minimize_to_tray"] = bool(self.minimize_to_tray)
        st["hold_tab_to_show"] = bool(self.hold_tab_mode)
        st["block_shift_tab"] = bool(self.block_shift_tab)
        st["panel_follow_tab"] = bool(self.panel_follow_tab)
        st["language"] = getattr(self, "language", _i18n.DEFAULT_LANG)

        st["types"] = self.types
        st["keybinds"] = self.binds

        # Persist hidden sets.
        st["hidden"] = {k: sorted(list(self.hidden_sets.get(k, set()))) for k in self.type_order}

        save_json(CONFIG_PATH, self.data)

    def _apply_rect(self):
        """
        Uses detected aspect label to select the correct ratio for the current map.
        """
        pm = self.data.get("profiles", {}).get(self.prof, {})
        rra = pm.get("rect_ratio_by_aspect", {})
        rr = rra.get(self.aspect, None)
        if not isinstance(rr, dict):
            rr = default_rect_ratio_by_aspect().get(self.aspect, default_rect_ratio_16_9())

        W, H = screenWH()
        self.rect = QtCore.QRect(
            int(rr["rx"] * W),
            int(rr["ry"] * H),
            max(1, int(rr["rw"] * W)),
            max(1, int(rr["rh"] * H))
        )
    
    def _position_panel_top_right(self):
        """Place the control panel against the top-right corner.

        Top-right keeps it clear of the central overlay marker band and of
        the game's trait/skill info (shown lower-right). Uses availableGeometry
        so the Windows taskbar is respected.
        """
        screen = QtGui.QGuiApplication.primaryScreen()
        if screen is None:
            self.panel.move(40, 40)
            return

        # Ensure the panel has computed its real size before we measure it.
        self.panel.adjustSize()
        avail = screen.availableGeometry()
        margin = 24
        pw = self.panel.frameGeometry().width()

        x = avail.right() - pw - margin
        y = avail.top() + margin
        # Never let the panel run off the left edge on small screens.
        x = max(avail.left() + margin, x)
        self.panel.move(int(x), int(y))

    def _set_overlay_to_primary_monitor(self):

        ps = QtGui.QGuiApplication.primaryScreen()

        if ps is None:

            return

        self.setGeometry(ps.geometry())



    def _show_overlay_on_primary(self):

        self._set_overlay_to_primary_monitor()

        self.show()

        topmost(int(self.winId()))

    def _set_num_switch(self, v: bool):
        self.num_sw = bool(v)
        self._save()

    def _type_toggle(self, tkey: str, enabled: bool):
        if tkey in self.types:
            self.types[tkey]["enabled"] = bool(enabled)
            self._save()
            self.update()

    def _type_color(self, tkey: str, color: QtGui.QColor):
        if tkey in self.types:
            self.types[tkey]["color"] = q2rgb(QtGui.QColor(color))
            self._save()
            self.update()

    def _scale_changed(self, scale: float):
        self.global_scale = float(scale)
        if self.global_scale < 0.10: self.global_scale = 0.10
        if self.global_scale > 5.00: self.global_scale = 5.00
        self._save()
        self.update()

    def _reset_colors(self):
        for k in self.type_order:
            self.types[k]["enabled"] = True
            self.types[k]["color"] = q2rgb(self.type_specs[k]["default_fill"])
            self.panel.setTypeState(k, True, self.type_specs[k]["default_fill"])
        self._save()
        self.update()

    def _reset_config_to_defaults(self):
        """
        Overwrites config.json with fresh defaults and reloads state immediately.
        This does not touch data.json or poiData.json.
        """
        fresh = build_default_config()
        save_json(CONFIG_PATH, fresh)

        self.data = load_or_replace_config()
        self._load_state_from_config(self.data)

        # Re apply map selection and rectangle because the selected map may have changed.
        self._apply_rect()

        # Push state back into GUI widgets.
        self.panel.chk_nums.setChecked(self.num_sw)
        self.panel.chk_tray.setChecked(self.minimize_to_tray)
        self.panel.chk_hold_tab.setChecked(self.hold_tab_mode)
        self.panel.chk_block_shift_tab.setChecked(self.block_shift_tab)
        self.panel.scale_box.setValue(float(self.global_scale))
        self.panel.setMap(self.prof)

        for k in self.type_order:
            self.panel.setTypeState(k, self.types[k]["enabled"], rgb2q(self.types[k]["color"], self.type_specs[k]["default_fill"]))

        # Refresh keybind labels.
        for action in self.binds:
            self.panel.setKeybindLabel(action, self._bind_label(action))

        # Apply overlay visibility state.
        (self.show if self.visible and self.master else self.hide)()
        self._save()
        self.update()

    def switch(self, name: str):
        if name in MAPS and name != self.prof:
            self.prof = name
            self._apply_rect()
            self._save()
            self.update()

    def _rebuild_all_caches(self):
        for m in MAPS:
            self.cache[m] = self._build_points_for_map(m)

    def _build_points_for_map(self, map_name: str):
        block = get_map_block(self.game_data, self.fmt, map_name)
        out = {k: [] for k in self.type_order}
        if not block:
            return out

        def build_for_category(cat: str):
            items = get_category_list(block, self.fmt, cat)
            # Append user-authored points for this map+category (drawn on top).
            user_pts = user_data.get_points(self.user_pois, map_name, cat)
            items = user_data.merge_into_points(items, user_pts)
            pts = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                c = it.get("c")
                if not c or len(c) < 2:
                    continue
                try:
                    x, y = float(c[0]), float(c[1])
                except:
                    continue
                u, v = rotate90cw_norm(x, y)
                pts.append({"u": u, "v": v, "x": x, "y": y, "raw": it, "src": cat})
            return pts

        for cat in self.type_order:
            if cat == "possible_xp":
                continue
            out[cat] = build_for_category(cat)

        union = []
        for src in ("towers", "big_towers", "armories"):
            union.extend(out.get(src, []))
        out["possible_xp"] = union

        return out

    def _hidden_key(self, tkey: str, pt: dict) -> str:
        """
        Stable hide id.
        For possible_xp we include src so hiding only affects possible_xp entries.
        For other categories use xi:yi.
        """
        xi = int(round(float(pt.get("x", 0))))
        yi = int(round(float(pt.get("y", 0))))
        if tkey == "possible_xp":
            src = str(pt.get("src", ""))
            return f"{src}:{xi}:{yi}"
        return f"{xi}:{yi}"

    def _is_hidden(self, tkey: str, pt: dict) -> bool:
        return self._hidden_key(tkey, pt) in self.hidden_sets.get(tkey, set())

    def _hide_hovered(self):
        if self.hover is None:
            return
        tkey = self.hover["type"]
        pt = self.hover["pt_ref"]
        hk = self._hidden_key(tkey, pt)
        self.hidden_sets.setdefault(tkey, set()).add(hk)
        self._save()
        self.hover = None
        self.update()

    def _update_hover(self):
        self.hover = None
        if not (self.master and self.visible and self.rect):
            return

        gp = QtGui.QCursor.pos()
        lp = self.mapFromGlobal(gp)
        mx, my = float(lp.x()), float(lp.y())

        pts_by_type = self.cache.get(self.prof, {})
        best = None
        best_d2 = float(self.hover_radius * self.hover_radius)

        for tkey in self.type_order:
            if not self.types.get(tkey, {}).get("enabled", True):
                continue

            for idx, pt in enumerate(pts_by_type.get(tkey, [])):
                if self._is_hidden(tkey, pt):
                    continue
                cx = self.rect.left() + pt["u"] * self.rect.width()
                cy = self.rect.top() + pt["v"] * self.rect.height()
                dx = mx - cx
                dy = my - cy
                d2 = dx * dx + dy * dy
                if d2 <= best_d2:
                    best_d2 = d2
                    best = {"map": self.prof, "type": tkey, "index": idx, "pt_ref": pt}

        self.hover = best

    def _tick_safe(self):
        try:
            self._tick()
        except Exception:
            print("覆盖层刷新出错：\n" + traceback.format_exc(), flush=True)

    def _tick(self):
        nm = self._bind_pressed("toggle_master")
        if nm and not self.p_toggle_master:
            self.master = not self.master
            if not self.master and self.visible:
                self.visible = False
                self.hide()
            self._save()
        self.p_toggle_master = nm

        nh = self._bind_pressed("hide_overlay")
        if nh and not self.p_hide and self.visible:
            self.visible = False
            self.hide()
            self._save()
        self.p_hide = nh

        if not self.master:
            return

        nt = self._bind_pressed("toggle_overlay")
        if self.hold_tab_mode:
            next_visible = bool(nt)
            if self.visible != next_visible:
                self.visible = next_visible
                if self.visible:
                    self._show_overlay_on_primary()
                else:
                    self.hide()
                self._sync_panel_visibility()
                self._save()
            self.p_toggle_overlay = nt
        else:
            if nt and not self.p_toggle_overlay:
                self.visible = not self.visible
                if self.visible:
                    self._show_overlay_on_primary()
                else:
                    self.hide()
                self._sync_panel_visibility()
                self._save()
            self.p_toggle_overlay = nt


        # Map switching uses MAPS order. Since MAPS changed, 2 is Lawson and 3 is DeSalle.
        if self.visible and self.num_sw:
            if self._bind_pressed("map_1"): self.switch(MAPS[0])
            elif self._bind_pressed("map_2"): self.switch(MAPS[1])
            elif self._bind_pressed("map_3"): self.switch(MAPS[2])
            elif self._bind_pressed("map_4"): self.switch(MAPS[3])

        if self.visible and (self._pick_mode or self._ruler_mode):
            self._poll_tool_cursor()
        elif self.visible:
            self._update_hover()
        elif self.hover is not None:
            self.hover = None

        hide_now = self._bind_pressed("hide_hovered")
        if hide_now and not self.p_hide_hovered:
            self._hide_hovered()
        self.p_hide_hovered = hide_now

        # Only repaint when something visible actually changed, instead of
        # forcing 60 fps of full redraws (which made hover feel laggy).
        # Pick/ruler modes drive small immediate repaints from cursor polling.
        hover_id = id(self.hover.get("pt_ref")) if self.hover else None
        if not self._pick_mode and not self._ruler_mode:
            if self.visible and hover_id != self._last_hover_id:
                self.update()
        self._last_hover_id = hover_id

    def _edit_keybind(self, action: str):
        """
        GUI initiated keybind edit.
        Captures next key press plus modifiers.
        Modifiers are only applied to hide_hovered by design.
        """
        d = KeyCaptureDialog(action_labels().get(action, action), self.panel)
        if ICON:
            d.setWindowIcon(QtGui.QIcon(ICON))

        if d.exec() != QtWidgets.QDialog.Accepted:
            return

        b = d.result_bind
        if not isinstance(b, dict) or action not in self.binds:
            return

        self.binds[action]["vk"] = int(b.get("vk", self.binds[action]["vk"]))

        if action == "hide_hovered":
            self.binds[action]["ctrl"] = bool(b.get("ctrl", True))
            self.binds[action]["alt"] = bool(b.get("alt", True))
            self.binds[action]["shift"] = bool(b.get("shift", True))

        self._save()
        self.panel.setKeybindLabel(action, self._bind_label(action))

    def paintEvent(self, ev):
        if not (self.master and self.visible and self.rect):
            return

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        pts_by_type = self.cache.get(self.prof, {})
        dirty_region = ev.region() if ev is not None else \
            QtGui.QRegion(QtCore.QRect(0, 0, max(1, self.width()), max(1, self.height())))

        for tkey in self.type_order:
            if not self.types.get(tkey, {}).get("enabled", True):
                continue

            fill = rgb2q(self.types[tkey].get("color"), self.type_specs[tkey]["default_fill"])
            border = self.type_specs[tkey]["border"]

            base_rpx = int(self.type_specs[tkey]["radius_px"])
            scaled = int(round(base_rpx * float(self.global_scale)))
            if scaled < 1: scaled = 1
            if scaled > 40: scaled = 40

            p.setPen(QtGui.QPen(border, 2))
            p.setBrush(fill)

            for pt in pts_by_type.get(tkey, []):
                if self._is_hidden(tkey, pt):
                    continue
                cx = self.rect.left() + pt["u"] * self.rect.width()
                cy = self.rect.top() + pt["v"] * self.rect.height()
                point_rect = QtCore.QRect(
                    int(cx - scaled - 3),
                    int(cy - scaled - 3),
                    int((scaled + 3) * 2),
                    int((scaled + 3) * 2),
                )
                if not dirty_region.intersects(point_rect):
                    continue
                p.drawEllipse(
                    QtCore.QPointF(cx, cy),
                    scaled, scaled
                )

        # Map label at top right.
        m = 20
        txt = f"{tr('Map')}：{map_display(self.prof)}  ({self.aspect})"
        f = p.font()
        f.setBold(True)
        p.setFont(f)
        fm = QtGui.QFontMetrics(f)
        tw, th = fm.horizontalAdvance(txt), fm.height()
        r = QtCore.QRectF(self.width() - m - tw - 16, m, tw + 16, th + 10)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QColor(0, 0, 0, 150))
        p.drawRoundedRect(r, 8, 8)
        p.setPen(QtGui.QPen(QtGui.QColor(230, 230, 230), 1))
        p.drawText(r.adjusted(8, 7, -8, -4), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, txt)

        # Pick mode overlay: rect outline, crosshair, live coords, preview dot.
        if self._pick_mode and self._pick_pos is not None:
            p.setPen(QtGui.QPen(QtGui.QColor(144, 160, 255), 1, QtCore.Qt.DashLine))
            p.setBrush(QtCore.Qt.NoBrush)
            p.drawRect(self.rect)

            px, py = self._pick_pos.x(), self._pick_pos.y()
            p.setPen(QtGui.QPen(QtGui.QColor(144, 160, 255), 1))
            p.drawLine(int(self.rect.left()), int(py), int(self.rect.right()), int(py))
            p.drawLine(int(px), int(self.rect.top()), int(px), int(self.rect.bottom()))

            # Preview dot at the cursor.
            p.setBrush(QtGui.QColor(255, 211, 77))
            p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
            p.drawEllipse(self._pick_pos, 5, 5)

            # Live grid coordinate next to the cursor.
            gx, gy = self._screen_to_grid(self._pick_pos)
            ctxt = f"X:{gx}  Y:{gy}"
            cfm = QtGui.QFontMetrics(p.font())
            ctw = cfm.horizontalAdvance(ctxt)
            cr = QtCore.QRectF(px + 12, py + 12, ctw + 12, cfm.height() + 6)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor(0, 0, 0, 180))
            p.drawRoundedRect(cr, 5, 5)
            p.setPen(QtGui.QPen(QtGui.QColor(255, 211, 77), 1))
            p.drawText(cr.adjusted(6, 3, -6, -3), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, ctxt)

        # Stored rulers for the current map.
        for ridx, item in self._iter_current_rulers():
            a = item.get("a")
            b = item.get("b")
            if not a or not b:
                continue
            ap = self._grid_to_screen_pos(a[0], a[1])
            bp = self._grid_to_screen_pos(b[0], b[1])
            p.setBrush(QtCore.Qt.NoBrush)
            p.setPen(QtGui.QPen(QtGui.QColor(100, 220, 180), 2))
            p.drawLine(int(ap.x()), int(ap.y()), int(bp.x()), int(bp.y()))
            p.setBrush(QtGui.QColor(100, 220, 180))
            p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1))
            p.drawEllipse(ap, 4, 4)
            p.drawEllipse(bp, 4, 4)

            rtxt = self._ruler_distance_text(a, b)
            rfm = QtGui.QFontMetrics(p.font())
            rtw = rfm.horizontalAdvance(rtxt)
            midx = (ap.x() + bp.x()) / 2
            midy = (ap.y() + bp.y()) / 2
            rr = QtCore.QRectF(midx - (rtw + 12) / 2, midy - rfm.height() - 10,
                               rtw + 12, rfm.height() + 6)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor(0, 0, 0, 170))
            p.drawRoundedRect(rr, 5, 5)
            p.setPen(QtGui.QPen(QtGui.QColor(100, 220, 180), 1))
            p.drawText(rr.adjusted(6, 3, -6, -3), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, rtxt)

        if self._ruler_mode and self._ruler_hover_delete is not None:
            idx, endpoint = self._ruler_hover_delete
            if 0 <= idx < len(self._rulers):
                ep = self._rulers[idx].get(endpoint)
                if ep:
                    sp = self._grid_to_screen_pos(ep[0], ep[1])
                    x, y = int(sp.x()), int(sp.y())
                    p.setBrush(QtGui.QColor(190, 45, 45, 220))
                    p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1))
                    p.drawEllipse(QtCore.QPointF(x, y), 10, 10)
                    p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
                    p.drawLine(x - 4, y - 4, x + 4, y + 4)
                    p.drawLine(x + 4, y - 4, x - 4, y + 4)

        # Ruler: line from the anchor to the cursor + distance (grid + ~meters).
        if self._ruler_mode and self._ruler_pos is not None:
            cur_gx, cur_gy = self._screen_to_grid(self._ruler_pos)
            cpx, cpy = self._ruler_pos.x(), self._ruler_pos.y()
            p.setBrush(QtCore.Qt.NoBrush)
            if self._ruler_a is not None:
                ax, ay = self._ruler_a
                # Anchor's screen position from its grid coords.
                au, av = rotate90cw_norm(ax, ay)
                apx = self.rect.left() + au * self.rect.width()
                apy = self.rect.top() + av * self.rect.height()
                p.setPen(QtGui.QPen(QtGui.QColor(255, 211, 77), 2))
                p.drawLine(int(apx), int(apy), int(cpx), int(cpy))
                p.setBrush(QtGui.QColor(255, 211, 77))
                p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1))
                p.drawEllipse(QtCore.QPointF(apx, apy), 4, 4)
                rtxt = self._ruler_distance_text((ax, ay), (cur_gx, cur_gy))
            else:
                rtxt = tr("Click to set start point")
            p.setBrush(QtGui.QColor(255, 211, 77))
            p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1))
            p.drawEllipse(self._ruler_pos, 4, 4)
            rfm = QtGui.QFontMetrics(p.font())
            rtw = rfm.horizontalAdvance(rtxt)
            rr = QtCore.QRectF(cpx + 12, cpy + 12, rtw + 12, rfm.height() + 6)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor(0, 0, 0, 190))
            p.drawRoundedRect(rr, 5, 5)
            p.setPen(QtGui.QPen(QtGui.QColor(255, 211, 77), 1))
            p.drawText(rr.adjusted(6, 3, -6, -3), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, rtxt)

        # Hover tooltip: show the description (and image count) of the point
        # under the cursor, if it has one. Skipped while picking.
        if not self._pick_mode and not self._ruler_mode and self.hover is not None:
            raw = self.hover.get("pt_ref", {}).get("raw", {})
            desc = str(raw.get("d", "")).strip() if isinstance(raw, dict) else ""
            imgs = raw.get("u", []) if isinstance(raw, dict) else []
            gp = QtGui.QCursor.pos()
            lp = self.mapFromGlobal(gp)
            hx, hy = lp.x(), lp.y()

            # Text bubble only when there is an actual description (no more
            # meaningless "[1]" image-count badge).
            bubble_top = hy - 6
            if desc:
                hfm = QtGui.QFontMetrics(p.font())
                hw = hfm.horizontalAdvance(desc)
                hr = QtCore.QRectF(hx + 14, hy - hfm.height() - 6, hw + 14, hfm.height() + 8)
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(QtGui.QColor(0, 0, 0, 190))
                p.drawRoundedRect(hr, 5, 5)
                p.setPen(QtGui.QPen(QtGui.QColor(235, 235, 235), 1))
                p.drawText(hr.adjusted(7, 4, -7, -4),
                           QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, desc)
                bubble_top = hr.top()

            # Reference image (downloaded on demand) shown above the bubble.
            pm = self._hover_pixmap(imgs)
            if pm is not None and not pm.isNull():
                iw, ih = pm.width(), pm.height()
                ix = hx + 14
                iy = bubble_top - ih - 6
                if iy < 4:  # not enough room above: place below the cursor
                    iy = hy + 18
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(QtGui.QColor(0, 0, 0, 200))
                p.drawRoundedRect(QtCore.QRectF(ix - 3, iy - 3, iw + 6, ih + 6), 5, 5)
                p.drawPixmap(int(ix), int(iy), pm)
            else:
                msg = self._hover_image_message(imgs)
                if msg:
                    sfm = QtGui.QFontMetrics(p.font())
                    sw = sfm.horizontalAdvance(msg)
                    sr = QtCore.QRectF(hx + 14, bubble_top - sfm.height() - 8,
                                       sw + 14, sfm.height() + 8)
                    p.setPen(QtCore.Qt.NoPen)
                    p.setBrush(QtGui.QColor(0, 0, 0, 190))
                    p.drawRoundedRect(sr, 5, 5)
                    color = QtGui.QColor(144, 160, 255) if "..." in msg else QtGui.QColor(255, 180, 120)
                    p.setPen(QtGui.QPen(color, 1))
                    p.drawText(sr.adjusted(7, 4, -7, -4),
                               QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, msg)

        p.end()
