"""Control panel window (Qt).

Verbatim move of the Panel class from the original single-file build.
Only imports changed: constants from huntoverlay.constants, key() from
huntoverlay.win32, DotChip from the sibling dialogs module.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from ..constants import APP_TITLE, MAPS
from ..i18n import map_display, tr, available_languages, get_language
from .. import boss_data
from ..win32 import key
from .dialogs import DotChip


class Panel(QtWidgets.QWidget):
    mapSel = QtCore.Signal(str)
    tnums = QtCore.Signal(bool)
    resetColors = QtCore.Signal()
    typeToggled = QtCore.Signal(str, bool)
    typeColor = QtCore.Signal(str, QtGui.QColor)
    scaleChanged = QtCore.Signal(float)

    requestBindEdit = QtCore.Signal(str)
    resetConfig = QtCore.Signal()
    minimizeToTrayChanged = QtCore.Signal(bool)
    holdTabModeChanged = QtCore.Signal(bool)
    blockShiftTabChanged = QtCore.Signal(bool)
    panelFollowTabChanged = QtCore.Signal(bool)
    forceRefresh = QtCore.Signal()
    languageChanged = QtCore.Signal(str)  # emits language code; applies on restart
    requestPoiEditor = QtCore.Signal(str)
    requestRuler = QtCore.Signal()
    requestClearRulers = QtCore.Signal()
    requestOpenDataDir = QtCore.Signal()


    def __init__(self, type_order, type_specs, start_scale: float, binds_label_map: dict, binds_current: dict, aspect: str, config_version: str, start_min_to_tray: bool, start_hold_tab_mode: bool, start_block_shift_tab: bool, start_panel_follow_tab: bool = False, p=None):
        super().__init__(p, QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(APP_TITLE)
        self.setFixedWidth(360)
        self.setStyleSheet(
            "QWidget{background:#1e1f22;color:#e6e6e6;font-size:12px;}"
            "QTabWidget::pane{border:1px solid #2b2d30;top:-1px;}"
            "QTabBar::tab{background:#2b2d30;color:#aaaaaa;padding:5px 14px;border:1px solid #3a3c40;border-bottom:none;}"
            "QTabBar::tab:selected{background:#1e1f22;color:#e6e6e6;}"
            "QTabBar::tab:hover{color:#e6e6e6;}"
            "QComboBox,QSpinBox,QDoubleSpinBox{background:#2b2d30;color:#e6e6e6;border:1px solid #3a3c40;padding:2px 4px;}"
            "QPushButton{background:#2b2d30;border:1px solid #3a3c40;padding:3px 8px;}"
            "QPushButton:hover{background:#34363a;}"
            "QPushButton:disabled{color:#555555;}"
            "QLabel{color:#cfd1d4;}"
            "QCheckBox{spacing:8px;}"
            "QCheckBox::indicator{width:14px;height:14px;}"
        )

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(0)

        tabs = QtWidgets.QTabWidget()
        outer.addWidget(tabs)

        # ── Tab 1: Types ──────────────────────────────────────────────
        types_page = QtWidgets.QWidget()
        tv = QtWidgets.QVBoxLayout(types_page)
        tv.setContentsMargins(8, 8, 8, 8)
        tv.setSpacing(2)

        self.type_widgets = {}
        for tkey in type_order:
            spec = type_specs[tkey]
            chk = QtWidgets.QCheckBox(spec["label"])
            chip = DotChip(spec["default_fill"], spec["border"])
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(4)
            row.addWidget(chk)
            row.addStretch(1)
            row.addWidget(chip)
            tv.addLayout(row)
            self.type_widgets[tkey] = (chk, chip)
            chk.toggled.connect(lambda val, k=tkey: self.typeToggled.emit(k, val))
            chip.changed.connect(lambda col, k=tkey: self.typeColor.emit(k, col))
            if tkey == "possible_xp":
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.HLine)
                line.setStyleSheet("background:#2b2d30;max-height:1px;margin:2px 0;")
                tv.addWidget(line)

        tv.addSpacing(6)

        # Bulk enable/disable all POI categories at once.
        sel_row = QtWidgets.QHBoxLayout()
        sel_row.setSpacing(6)
        btn_all = QtWidgets.QPushButton(tr("Select All"))
        btn_none = QtWidgets.QPushButton(tr("Deselect All"))
        btn_all.clicked.connect(lambda: self._set_all_types(True))
        btn_none.clicked.connect(lambda: self._set_all_types(False))
        sel_row.addWidget(btn_all)
        sel_row.addWidget(btn_none)
        tv.addLayout(sel_row)

        map_row = QtWidgets.QHBoxLayout()
        map_row.addWidget(QtWidgets.QLabel(tr("Map:")))
        self.cmb = QtWidgets.QComboBox()
        # Show Chinese labels but keep the English canonical name as item data,
        # so the rest of the app keeps receiving English map keys.
        for m in MAPS:
            self.cmb.addItem(map_display(m), m)
        map_row.addWidget(self.cmb, 1)
        tv.addLayout(map_row)
        self.cmb.currentIndexChanged.connect(
            lambda _i: self.mapSel.emit(self.cmb.currentData())
        )

        self.chk_nums = QtWidgets.QCheckBox(tr("1-4 map switch keys"))
        tv.addWidget(self.chk_nums)
        self.chk_nums.toggled.connect(self.tnums)

        tv.addSpacing(6)

        scale_row = QtWidgets.QHBoxLayout()
        scale_row.addWidget(QtWidgets.QLabel(tr("Scale:")))
        self.btn_dec = QtWidgets.QPushButton("−")
        self.btn_dec.setFixedWidth(26)
        self.btn_inc = QtWidgets.QPushButton("+")
        self.btn_inc.setFixedWidth(26)
        self.scale_box = QtWidgets.QDoubleSpinBox()
        self.scale_box.setRange(0.10, 5.00)
        self.scale_box.setDecimals(2)
        self.scale_box.setSingleStep(0.05)
        self.scale_box.setValue(float(start_scale))
        self.scale_box.setFixedWidth(68)
        scale_row.addWidget(self.btn_dec)
        scale_row.addWidget(self.btn_inc)
        scale_row.addStretch(1)
        scale_row.addWidget(self.scale_box)
        tv.addLayout(scale_row)
        self.btn_dec.clicked.connect(self._dec_scale)
        self.btn_inc.clicked.connect(self._inc_scale)
        self.scale_box.valueChanged.connect(lambda x: self.scaleChanged.emit(float(x)))

        tv.addSpacing(6)
        self.btn_def_colors = QtWidgets.QPushButton(tr("Reset Colors"))
        tv.addWidget(self.btn_def_colors)
        self.btn_def_colors.clicked.connect(self.resetColors)

        poi_type_row = QtWidgets.QHBoxLayout()
        poi_type_row.addWidget(QtWidgets.QLabel(tr("POI type:")))
        self.cmb_poi_type = QtWidgets.QComboBox()
        for tkey in type_order:
            if tkey == "possible_xp":
                continue
            self.cmb_poi_type.addItem(type_specs[tkey]["label"], tkey)
        poi_type_row.addWidget(self.cmb_poi_type, 1)
        tv.addLayout(poi_type_row)

        self.btn_edit_pois = QtWidgets.QPushButton(tr("Edit POIs"))
        tv.addWidget(self.btn_edit_pois)
        self.btn_edit_pois.clicked.connect(self._emit_poi_editor_request)

        self.btn_ruler = QtWidgets.QPushButton(tr("Ruler"))
        tv.addWidget(self.btn_ruler)
        self.btn_ruler.clicked.connect(self.requestRuler)

        self.btn_clear_rulers = QtWidgets.QPushButton(tr("Clear Rulers"))
        tv.addWidget(self.btn_clear_rulers)
        self.btn_clear_rulers.clicked.connect(self.requestClearRulers)

        tv.addStretch(1)
        tabs.addTab(types_page, tr("POIs"))

        # ── Tab 2: Keybinds ───────────────────────────────────────────
        kb_page = QtWidgets.QWidget()
        kv = QtWidgets.QVBoxLayout(kb_page)
        kv.setContentsMargins(8, 8, 8, 8)
        kv.setSpacing(4)

        self.kb_rows = {}
        for action, label in binds_label_map.items():
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label))
            row.addStretch(1)
            cur_lbl = QtWidgets.QLabel(binds_current.get(action, ""))
            cur_lbl.setStyleSheet("color:#90a0ff;")
            cur_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            row.addWidget(cur_lbl)
            btn = QtWidgets.QPushButton(tr("Set"))
            btn.setFixedWidth(48)
            row.addWidget(btn)
            kv.addLayout(row)
            self.kb_rows[action] = (btn, cur_lbl)
            btn.clicked.connect(lambda _, a=action: self.requestBindEdit.emit(a))

        kv.addStretch(1)
        tabs.addTab(kb_page, tr("Keybinds"))

        # ── Tab 3: Settings ───────────────────────────────────────────
        cfg_page = QtWidgets.QWidget()
        cv = QtWidgets.QVBoxLayout(cfg_page)
        cv.setContentsMargins(8, 8, 8, 8)
        cv.setSpacing(6)

        # Language selector (change applies on restart).
        lang_row = QtWidgets.QHBoxLayout()
        lang_row.addWidget(QtWidgets.QLabel(tr("Language:")))
        self.cmb_lang = QtWidgets.QComboBox()
        for code, display in available_languages():
            self.cmb_lang.addItem(display, code)
        cur = self.cmb_lang.findData(get_language())
        if cur >= 0:
            self.cmb_lang.setCurrentIndex(cur)
        lang_row.addWidget(self.cmb_lang, 1)
        cv.addLayout(lang_row)
        self.cmb_lang.currentIndexChanged.connect(
            lambda _i: self.languageChanged.emit(self.cmb_lang.currentData())
        )
        self.lbl_lang_hint = QtWidgets.QLabel(tr("Restart to apply the language change."))
        self.lbl_lang_hint.setStyleSheet("color:#90a0ff;")
        self.lbl_lang_hint.setVisible(False)
        cv.addWidget(self.lbl_lang_hint)

        self.chk_tray = QtWidgets.QCheckBox(tr("Minimize to system tray"))
        self.chk_tray.setChecked(bool(start_min_to_tray))
        cv.addWidget(self.chk_tray)
        self.chk_tray.toggled.connect(lambda b: self.minimizeToTrayChanged.emit(bool(b)))

        self.chk_hold_tab = QtWidgets.QCheckBox(tr("Hold Tab to show overlay"))
        self.chk_hold_tab.setChecked(bool(start_hold_tab_mode))
        cv.addWidget(self.chk_hold_tab)
        self.chk_hold_tab.toggled.connect(lambda b: self.holdTabModeChanged.emit(bool(b)))

        self.chk_block_shift_tab = QtWidgets.QCheckBox(tr("Block Shift+Tab"))
        self.chk_block_shift_tab.setChecked(bool(start_block_shift_tab))
        cv.addWidget(self.chk_block_shift_tab)
        self.chk_block_shift_tab.toggled.connect(lambda b: self.blockShiftTabChanged.emit(bool(b)))

        self.chk_panel_follow_tab = QtWidgets.QCheckBox(tr("Panel follows Tab (show/hide with overlay)"))
        self.chk_panel_follow_tab.setChecked(bool(start_panel_follow_tab))
        cv.addWidget(self.chk_panel_follow_tab)
        self.chk_panel_follow_tab.toggled.connect(lambda b: self.panelFollowTabChanged.emit(bool(b)))

        cv.addSpacing(4)
        self.btn_reset_cfg = QtWidgets.QPushButton(tr("Reset to Default Config"))
        cv.addWidget(self.btn_reset_cfg)
        self.btn_reset_cfg.clicked.connect(self.resetConfig)

        self.btn_open_data_dir = QtWidgets.QPushButton(tr("Open Data Folder"))
        cv.addWidget(self.btn_open_data_dir)
        self.btn_open_data_dir.clicked.connect(self.requestOpenDataDir)

        cv.addSpacing(8)

        update_row = QtWidgets.QHBoxLayout()
        self.update_label = QtWidgets.QLabel(tr("Data: checking..."))
        self.update_label.setStyleSheet("color:#666666;font-size:11px;")
        update_row.addWidget(self.update_label)
        update_row.addStretch(1)
        self.btn_force_refresh = QtWidgets.QPushButton(tr("Refresh Data"))
        self.btn_force_refresh.setFixedWidth(92)
        update_row.addWidget(self.btn_force_refresh)
        cv.addLayout(update_row)
        self.btn_force_refresh.clicked.connect(self.forceRefresh)

        cv.addSpacing(2)
        info_style = "color:#555555;font-size:11px;"
        lbl_info = QtWidgets.QLabel(f"{tr('Aspect:')}{aspect}  |  v{config_version}")
        lbl_info.setStyleSheet(info_style)
        cv.addWidget(lbl_info)
        lbl_path = QtWidgets.QLabel("%LOCALAPPDATA%\\HuntOverlay")
        lbl_path.setStyleSheet(info_style)
        cv.addWidget(lbl_path)

        cv.addStretch(1)
        tabs.addTab(cfg_page, tr("Settings"))

        # ── Tab 4: Bosses (reference) ─────────────────────────────────
        tabs.addTab(self._build_boss_tab(), tr("Bosses"))

    def _build_boss_tab(self):
        """Read-only boss reference: fire/poison resistance + fight tips."""
        page = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        inner = QtWidgets.QWidget()
        bv = QtWidgets.QVBoxLayout(inner)
        bv.setContentsMargins(8, 8, 8, 8)
        bv.setSpacing(10)

        res_color = {
            boss_data.WEAK: "#7ee787",     # green: exploitable
            boss_data.IMMUNE: "#ff7b72",   # red: useless
            boss_data.NORMAL: "#9aa0a6",   # gray: no special interaction
        }
        res_label = {
            boss_data.WEAK: tr("Weak"),
            boss_data.IMMUNE: tr("Immune"),
            boss_data.NORMAL: tr("Normal"),
        }

        for key in boss_data.boss_keys():
            b = boss_data.get_boss(key)
            if not b:
                continue
            card = QtWidgets.QFrame()
            card.setStyleSheet("QFrame{background:#242629;border:1px solid #3a3c40;border-radius:6px;}")
            cl = QtWidgets.QVBoxLayout(card)
            cl.setContentsMargins(10, 8, 10, 8)
            cl.setSpacing(4)

            title = QtWidgets.QLabel(tr(b["name"]))
            title.setStyleSheet("font-size:14px;font-weight:bold;color:#e6e6e6;border:0;")
            cl.addWidget(title)

            # Resistances line.
            res_row = QtWidgets.QHBoxLayout()
            res_row.setSpacing(12)
            for dmg_key, dmg_name in (("fire", tr("Fire")), ("poison", tr("Poison"))):
                val = b.get(dmg_key, boss_data.NORMAL)
                lab = QtWidgets.QLabel(f"{dmg_name}: {res_label[val]}")
                lab.setStyleSheet(f"color:{res_color[val]};border:0;")
                res_row.addWidget(lab)
            res_row.addStretch(1)
            cl.addLayout(res_row)

            for tip in b.get("tips", []):
                t = QtWidgets.QLabel("• " + tr(tip))
                t.setWordWrap(True)
                t.setStyleSheet("color:#cfd1d4;border:0;")
                cl.addWidget(t)

            bv.addWidget(card)

        note = QtWidgets.QLabel(tr("Banish time and exact HP vary by patch and are omitted."))
        note.setWordWrap(True)
        note.setStyleSheet("color:#8a8d93;")
        bv.addWidget(note)
        bv.addStretch(1)

        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    def _dec_scale(self):
        self.scale_box.setValue(max(self.scale_box.minimum(), self.scale_box.value() - 0.05))

    def _inc_scale(self):
        self.scale_box.setValue(min(self.scale_box.maximum(), self.scale_box.value() + 0.05))

    def _emit_poi_editor_request(self):
        category = self.cmb_poi_type.currentData()
        self.requestPoiEditor.emit(str(category or ""))

    def setTypeState(self, tkey: str, enabled: bool, fill_color: QtGui.QColor):
        chk, chip = self.type_widgets[tkey]
        chk.blockSignals(True)
        chip.blockSignals(True)
        chk.setChecked(bool(enabled))
        chip.setFill(fill_color)
        chip.blockSignals(False)
        chk.blockSignals(False)

    def _set_all_types(self, enabled: bool):
        """Check or uncheck every POI category at once.

        Signals are left unblocked so each real state change emits typeToggled
        and the overlay/config update accordingly. setChecked is a no-op (emits
        nothing) for boxes already in the target state.
        """
        for chk, _chip in self.type_widgets.values():
            chk.setChecked(bool(enabled))

    def setMap(self, name: str):
        # name is the English canonical key; items store it as item data.
        i = self.cmb.findData(name)
        if i >= 0:
            self.cmb.blockSignals(True)
            self.cmb.setCurrentIndex(i)
            self.cmb.blockSignals(False)

    def setLastUpdateText(self, txt: str):
        self.update_label.setText(txt)

    def setKeybindLabel(self, action: str, txt: str):
        entry = self.kb_rows.get(action)
        if entry:
            entry[1].setText(txt)
