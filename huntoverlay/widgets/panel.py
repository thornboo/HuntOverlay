"""QML-backed, resizable control center for HuntOverlay."""

from pathlib import Path

from PySide6 import QtCore, QtGui, QtQuickWidgets, QtWidgets

from .. import boss_data
from ..constants import APP_TITLE, MAPS
from ..i18n import available_languages, get_language, map_display, tr
from ..paths import bd


def centered_window_position(
    available: QtCore.QRect,
    window_size: QtCore.QSize,
    margin: int = 24,
) -> QtCore.QPoint:
    """Return a centered, screen-safe top-left position."""
    safe_margin = max(0, int(margin))
    left = available.left() + safe_margin
    top = available.top() + safe_margin
    usable_width = max(1, available.width() - safe_margin * 2)
    usable_height = max(1, available.height() - safe_margin * 2)
    width = max(1, int(window_size.width()))
    height = max(1, int(window_size.height()))

    x = available.left() + (available.width() - width) // 2
    y = available.top() + (available.height() - height) // 2
    max_x = left + max(0, usable_width - width)
    max_y = top + max(0, usable_height - height)
    return QtCore.QPoint(
        max(left, min(x, max_x)),
        max(top, min(y, max_y)),
    )


def _color_name(value) -> str:
    color = value if isinstance(value, QtGui.QColor) else QtGui.QColor(value)
    return color.name(QtGui.QColor.HexRgb)


class Panel(QtWidgets.QWidget):
    """Stable QWidget window shell hosting the QML control-center view."""

    mapSel = QtCore.Signal(str)
    tnums = QtCore.Signal(bool)
    resetColors = QtCore.Signal()
    typeToggled = QtCore.Signal(str, bool)
    typeColor = QtCore.Signal(str, QtGui.QColor)
    scaleChanged = QtCore.Signal(float)

    requestBindEdit = QtCore.Signal(str)
    resetConfig = QtCore.Signal()
    trayIconChanged = QtCore.Signal(bool)
    minimizeToTrayChanged = QtCore.Signal(bool)
    startHiddenToTrayChanged = QtCore.Signal(bool)
    holdTabModeChanged = QtCore.Signal(bool)
    blockShiftTabChanged = QtCore.Signal(bool)
    panelFollowTabChanged = QtCore.Signal(bool)
    forceRefresh = QtCore.Signal()
    languageChanged = QtCore.Signal(str)
    requestPoiEditor = QtCore.Signal(str)
    requestPoiPick = QtCore.Signal(str)
    customPoiContextChanged = QtCore.Signal()
    userPoisToggled = QtCore.Signal(bool)
    requestRuler = QtCore.Signal()
    requestClearRulers = QtCore.Signal()
    requestOpenDataDir = QtCore.Signal()

    mapStateChanged = QtCore.Signal()
    scaleStateChanged = QtCore.Signal()
    typeItemsChanged = QtCore.Signal()
    customPoiStateChanged = QtCore.Signal()
    keybindItemsChanged = QtCore.Signal()
    settingsStateChanged = QtCore.Signal()
    statusStateChanged = QtCore.Signal()

    DEFAULT_SIZE = QtCore.QSize(1040, 660)
    MINIMUM_SIZE = QtCore.QSize(760, 480)

    def __init__(
        self,
        type_order,
        type_specs,
        start_scale: float,
        binds_label_map: dict,
        binds_current: dict,
        aspect: str,
        config_version: str,
        start_min_to_tray: bool,
        start_hold_tab_mode: bool,
        start_block_shift_tab: bool,
        start_panel_follow_tab: bool = False,
        start_show_user_pois: bool = True,
        start_show_tray_icon: bool = False,
        start_start_hidden_to_tray: bool = False,
        p=None,
    ):
        super().__init__(
            p,
            QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint,
        )
        self.setObjectName("controlCenter")
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(self.MINIMUM_SIZE)
        self.resize(self.DEFAULT_SIZE)

        self._type_order = list(type_order)
        self._type_specs = dict(type_specs)
        self._map_options = [
            {"label": map_display(name), "value": name} for name in MAPS
        ]
        self._current_map_index = 0
        self._scale_value = min(5.0, max(0.1, float(start_scale)))
        self._number_switch_enabled = False
        self._type_items = [
            {
                "key": key,
                "label": self._type_specs[key]["label"],
                "enabled": False,
                "fill": _color_name(self._type_specs[key]["default_fill"]),
                "border": _color_name(self._type_specs[key]["border"]),
            }
            for key in self._type_order
        ]
        self._custom_poi_options = [
            {
                "label": self._type_specs[key]["label"],
                "value": key,
            }
            for key in self._type_order
            if key != "possible_xp"
        ]
        self._current_poi_type_index = 0
        self._custom_poi_count_text = ""
        self._user_pois_enabled = bool(start_show_user_pois)

        self._keybind_items = [
            {
                "action": action,
                "label": label,
                "value": binds_current.get(action, ""),
            }
            for action, label in binds_label_map.items()
        ]
        self._language_options = [
            {"label": label, "value": code}
            for code, label in available_languages()
        ]
        language_codes = [
            item["value"] for item in self._language_options
        ]
        try:
            self._current_language_index = language_codes.index(
                get_language()
            )
        except ValueError:
            self._current_language_index = 0

        self._aspect_label = str(aspect)
        self._config_version = str(config_version)
        self._tray_icon_enabled = bool(start_show_tray_icon)
        self._minimize_to_tray_enabled = bool(start_min_to_tray)
        self._start_hidden_to_tray_enabled = bool(
            start_start_hidden_to_tray
        )
        self._hold_tab_mode_enabled = bool(start_hold_tab_mode)
        self._block_shift_tab_enabled = bool(start_block_shift_tab)
        self._panel_follow_tab_enabled = bool(start_panel_follow_tab)
        self._language_hint_visible = False
        self._status_text = tr("Data: checking...")
        self._force_refresh_enabled = True
        self._boss_items = self._build_boss_items()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.qml_view = QtQuickWidgets.QQuickWidget(self)
        self.qml_view.setObjectName("controlCenterQmlView")
        self.qml_view.setResizeMode(
            QtQuickWidgets.QQuickWidget.SizeRootObjectToView
        )
        self.qml_view.setClearColor(QtGui.QColor("#202020"))
        self.qml_view.rootContext().setContextProperty(
            "panelBridge",
            self,
        )
        self.qml_view.setSource(
            QtCore.QUrl.fromLocalFile(str(self._qml_source_path()))
        )
        if self.qml_view.status() == QtQuickWidgets.QQuickWidget.Error:
            details = "\n".join(
                error.toString() for error in self.qml_view.errors()
            )
            raise RuntimeError(
                f"Failed to load HuntOverlay control-center QML:\n{details}"
            )
        layout.addWidget(self.qml_view)

    @staticmethod
    def _qml_source_path() -> Path:
        candidates = (
            Path(bd()) / "huntoverlay" / "qml" / "ControlCenter.qml",
            Path(__file__).resolve().parents[1] / "qml" / "ControlCenter.qml",
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(
            "ControlCenter.qml was not found in the source or bundle."
        )

    @staticmethod
    def _resistance_color(value: str) -> str:
        return {
            boss_data.WEAK: "#6CCB5F",
            boss_data.IMMUNE: "#FF6B5F",
            boss_data.NORMAL: "#9D9D9D",
        }.get(value, "#9D9D9D")

    def _build_boss_items(self) -> list[dict]:
        labels = {
            boss_data.WEAK: tr("Weak"),
            boss_data.IMMUNE: tr("Immune"),
            boss_data.NORMAL: tr("Normal"),
        }
        items = []
        for key in boss_data.boss_keys():
            record = boss_data.get_boss(key)
            if not record:
                continue
            fire = record.get("fire", boss_data.NORMAL)
            poison = record.get("poison", boss_data.NORMAL)
            items.append(
                {
                    "key": key,
                    "name": tr(record["name"]),
                    "fireLabel": labels[fire],
                    "fireColor": self._resistance_color(fire),
                    "poisonLabel": labels[poison],
                    "poisonColor": self._resistance_color(poison),
                    "tips": [tr(tip) for tip in record.get("tips", [])],
                }
            )
        return items

    @QtCore.Slot(str, result=str)
    def uiText(self, key: str) -> str:
        return tr(str(key))

    @QtCore.Property("QVariantList", constant=True)
    def mapOptions(self):
        return self._map_options

    @QtCore.Property(int, notify=mapStateChanged)
    def currentMapIndex(self) -> int:
        return self._current_map_index

    @QtCore.Property(str, notify=mapStateChanged)
    def currentMapLabel(self) -> str:
        return self._map_options[self._current_map_index]["label"]

    @QtCore.Property(float, notify=scaleStateChanged)
    def scaleValue(self) -> float:
        return self._scale_value

    @QtCore.Property(bool, notify=settingsStateChanged)
    def numberSwitchEnabled(self) -> bool:
        return self._number_switch_enabled

    @QtCore.Property(int, constant=True)
    def typeCount(self) -> int:
        return len(self._type_items)

    @QtCore.Property("QVariantList", notify=typeItemsChanged)
    def typeItems(self):
        return self._type_items

    @QtCore.Property("QVariantList", constant=True)
    def customPoiOptions(self):
        return self._custom_poi_options

    @QtCore.Property(int, notify=customPoiStateChanged)
    def currentPoiTypeIndex(self) -> int:
        return self._current_poi_type_index

    @QtCore.Property(str, notify=customPoiStateChanged)
    def customPoiCountText(self) -> str:
        return self._custom_poi_count_text

    @QtCore.Property(bool, notify=settingsStateChanged)
    def userPoisEnabled(self) -> bool:
        return self._user_pois_enabled

    @QtCore.Property("QVariantList", notify=keybindItemsChanged)
    def keybindItems(self):
        return self._keybind_items

    @QtCore.Property("QVariantList", constant=True)
    def languageOptions(self):
        return self._language_options

    @QtCore.Property(int, notify=settingsStateChanged)
    def currentLanguageIndex(self) -> int:
        return self._current_language_index

    @QtCore.Property(str, constant=True)
    def aspectLabel(self) -> str:
        return self._aspect_label

    @QtCore.Property(str, constant=True)
    def configVersion(self) -> str:
        return self._config_version

    @QtCore.Property(bool, notify=settingsStateChanged)
    def trayIconEnabled(self) -> bool:
        return self._tray_icon_enabled

    @QtCore.Property(bool, notify=settingsStateChanged)
    def minimizeToTrayEnabled(self) -> bool:
        return self._minimize_to_tray_enabled

    @QtCore.Property(bool, notify=settingsStateChanged)
    def startHiddenToTrayEnabled(self) -> bool:
        return self._start_hidden_to_tray_enabled

    @QtCore.Property(bool, notify=settingsStateChanged)
    def holdTabModeEnabled(self) -> bool:
        return self._hold_tab_mode_enabled

    @QtCore.Property(bool, notify=settingsStateChanged)
    def blockShiftTabEnabled(self) -> bool:
        return self._block_shift_tab_enabled

    @QtCore.Property(bool, notify=settingsStateChanged)
    def panelFollowTabEnabled(self) -> bool:
        return self._panel_follow_tab_enabled

    @QtCore.Property(bool, notify=settingsStateChanged)
    def languageHintVisible(self) -> bool:
        return self._language_hint_visible

    @QtCore.Property(str, notify=statusStateChanged)
    def statusText(self) -> str:
        return self._status_text

    @QtCore.Property(bool, notify=statusStateChanged)
    def forceRefreshEnabled(self) -> bool:
        return self._force_refresh_enabled

    @QtCore.Property("QVariantList", constant=True)
    def bossItems(self):
        return self._boss_items

    @QtCore.Slot(int)
    def selectMap(self, index: int) -> None:
        if not (0 <= index < len(self._map_options)):
            return
        if index == self._current_map_index:
            return
        self._current_map_index = index
        self.mapStateChanged.emit()
        self.mapSel.emit(self._map_options[index]["value"])

    @QtCore.Slot(float)
    def adjustScale(self, delta: float) -> None:
        self._set_scale(self._scale_value + float(delta), emit=True)

    def _set_scale(self, value: float, *, emit: bool) -> None:
        next_value = round(min(5.0, max(0.1, float(value))), 2)
        if next_value == self._scale_value:
            return
        self._scale_value = next_value
        self.scaleStateChanged.emit()
        if emit:
            self.scaleChanged.emit(next_value)

    @QtCore.Slot(bool)
    def setNumberSwitchFromUi(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._number_switch_enabled:
            return
        self._number_switch_enabled = enabled
        self.settingsStateChanged.emit()
        self.tnums.emit(enabled)

    @QtCore.Slot(str, bool)
    def setTypeEnabledFromUi(self, key: str, enabled: bool) -> None:
        item = self._type_item(str(key))
        if item is None or bool(item["enabled"]) == bool(enabled):
            return
        item["enabled"] = bool(enabled)
        self.typeItemsChanged.emit()
        self.typeToggled.emit(str(key), bool(enabled))

    @QtCore.Slot(bool)
    def setAllTypesFromUi(self, enabled: bool) -> None:
        changed_keys = []
        for item in self._type_items:
            if bool(item["enabled"]) == bool(enabled):
                continue
            item["enabled"] = bool(enabled)
            changed_keys.append(item["key"])
        if not changed_keys:
            return
        self.typeItemsChanged.emit()
        for key in changed_keys:
            self.typeToggled.emit(key, bool(enabled))

    @QtCore.Slot()
    def requestResetColorsFromUi(self) -> None:
        self.resetColors.emit()

    @QtCore.Slot(str)
    def chooseTypeColor(self, key: str) -> None:
        item = self._type_item(str(key))
        if item is None:
            return
        selected = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(item["fill"]),
            self,
            tr("Choose marker color"),
        )
        if not selected.isValid():
            return
        next_fill = _color_name(selected)
        if next_fill == item["fill"]:
            return
        item["fill"] = next_fill
        self.typeItemsChanged.emit()
        self.typeColor.emit(str(key), selected)

    @QtCore.Slot(int)
    def selectPoiType(self, index: int) -> None:
        if not (0 <= index < len(self._custom_poi_options)):
            return
        if index == self._current_poi_type_index:
            return
        self._current_poi_type_index = index
        self.customPoiStateChanged.emit()
        self.customPoiContextChanged.emit()

    @QtCore.Slot()
    def requestPoiPickFromUi(self) -> None:
        self.requestPoiPick.emit(self.currentPoiType())

    @QtCore.Slot()
    def requestPoiEditorFromUi(self) -> None:
        self.requestPoiEditor.emit(self.currentPoiType())

    @QtCore.Slot(bool)
    def setUserPoisFromUi(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._user_pois_enabled:
            return
        self._user_pois_enabled = enabled
        self.settingsStateChanged.emit()
        self.userPoisToggled.emit(enabled)

    @QtCore.Slot()
    def requestRulerFromUi(self) -> None:
        self.requestRuler.emit()

    @QtCore.Slot()
    def requestClearRulersFromUi(self) -> None:
        self.requestClearRulers.emit()

    @QtCore.Slot(str)
    def requestBindEditFromUi(self, action: str) -> None:
        self.requestBindEdit.emit(str(action))

    @QtCore.Slot(int)
    def selectLanguage(self, index: int) -> None:
        if not (0 <= index < len(self._language_options)):
            return
        if index == self._current_language_index:
            return
        self._current_language_index = index
        self.settingsStateChanged.emit()
        self.languageChanged.emit(self._language_options[index]["value"])

    @QtCore.Slot(bool)
    def setTrayIconFromUi(self, enabled: bool) -> None:
        self._set_flag(
            "_tray_icon_enabled",
            enabled,
            self.trayIconChanged,
        )

    @QtCore.Slot(bool)
    def setMinimizeToTrayFromUi(self, enabled: bool) -> None:
        self._set_flag(
            "_minimize_to_tray_enabled",
            enabled,
            self.minimizeToTrayChanged,
        )

    @QtCore.Slot(bool)
    def setStartHiddenToTrayFromUi(self, enabled: bool) -> None:
        self._set_flag(
            "_start_hidden_to_tray_enabled",
            enabled,
            self.startHiddenToTrayChanged,
        )

    @QtCore.Slot(bool)
    def setHoldTabModeFromUi(self, enabled: bool) -> None:
        self._set_flag(
            "_hold_tab_mode_enabled",
            enabled,
            self.holdTabModeChanged,
        )

    @QtCore.Slot(bool)
    def setBlockShiftTabFromUi(self, enabled: bool) -> None:
        self._set_flag(
            "_block_shift_tab_enabled",
            enabled,
            self.blockShiftTabChanged,
        )

    @QtCore.Slot(bool)
    def setPanelFollowTabFromUi(self, enabled: bool) -> None:
        self._set_flag(
            "_panel_follow_tab_enabled",
            enabled,
            self.panelFollowTabChanged,
        )

    @QtCore.Slot()
    def requestOpenDataDirFromUi(self) -> None:
        self.requestOpenDataDir.emit()

    @QtCore.Slot()
    def requestResetConfigFromUi(self) -> None:
        self.resetConfig.emit()

    @QtCore.Slot()
    def requestForceRefreshFromUi(self) -> None:
        self.forceRefresh.emit()

    def _set_flag(self, name: str, enabled: bool, event_signal=None) -> None:
        enabled = bool(enabled)
        if bool(getattr(self, name)) == enabled:
            return
        setattr(self, name, enabled)
        self.settingsStateChanged.emit()
        if event_signal is not None:
            event_signal.emit(enabled)

    def _type_item(self, key: str):
        return next(
            (item for item in self._type_items if item["key"] == key),
            None,
        )

    def setTypeState(
        self,
        tkey: str,
        enabled: bool,
        fill_color: QtGui.QColor,
    ) -> None:
        item = self._type_item(str(tkey))
        if item is None:
            return
        next_fill = _color_name(fill_color)
        if (
            bool(item["enabled"]) == bool(enabled)
            and item["fill"] == next_fill
        ):
            return
        item["enabled"] = bool(enabled)
        item["fill"] = next_fill
        self.typeItemsChanged.emit()

    def setMap(self, name: str) -> None:
        names = [item["value"] for item in self._map_options]
        try:
            index = names.index(str(name))
        except ValueError:
            return
        if index == self._current_map_index:
            return
        self._current_map_index = index
        self.mapStateChanged.emit()

    def setLastUpdateText(self, txt: str) -> None:
        txt = str(txt)
        if txt == self._status_text:
            return
        self._status_text = txt
        self.statusStateChanged.emit()

    def setCustomPoiCounts(self, current: int, total: int) -> None:
        text = (
            f"{tr('Current category:')} {int(current)}  |  "
            f"{tr('All custom:')} {int(total)}"
        )
        if text == self._custom_poi_count_text:
            return
        self._custom_poi_count_text = text
        self.customPoiStateChanged.emit()

    def setKeybindLabel(self, action: str, txt: str) -> None:
        for item in self._keybind_items:
            if item["action"] != action:
                continue
            if item["value"] == str(txt):
                return
            item["value"] = str(txt)
            self.keybindItemsChanged.emit()
            return

    def setNumberSwitchEnabled(self, enabled: bool) -> None:
        self._set_flag("_number_switch_enabled", enabled)

    def setTrayIconEnabled(self, enabled: bool) -> None:
        self._set_flag("_tray_icon_enabled", enabled)

    def setMinimizeToTrayEnabled(self, enabled: bool) -> None:
        self._set_flag("_minimize_to_tray_enabled", enabled)

    def setStartHiddenToTrayEnabled(self, enabled: bool) -> None:
        self._set_flag("_start_hidden_to_tray_enabled", enabled)

    def setHoldTabModeEnabled(self, enabled: bool) -> None:
        self._set_flag("_hold_tab_mode_enabled", enabled)

    def setBlockShiftTabEnabled(self, enabled: bool) -> None:
        self._set_flag("_block_shift_tab_enabled", enabled)

    def setPanelFollowTabEnabled(self, enabled: bool) -> None:
        self._set_flag("_panel_follow_tab_enabled", enabled)

    def setUserPoisEnabled(self, enabled: bool) -> None:
        self._set_flag("_user_pois_enabled", enabled)

    def setScale(self, value: float) -> None:
        self._set_scale(value, emit=False)

    def setForceRefreshEnabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._force_refresh_enabled:
            return
        self._force_refresh_enabled = enabled
        self.statusStateChanged.emit()

    def setLanguageHintVisible(self, visible: bool) -> None:
        visible = bool(visible)
        if visible == self._language_hint_visible:
            return
        self._language_hint_visible = visible
        self.settingsStateChanged.emit()

    @QtCore.Slot(result=str)
    def currentPoiType(self) -> str:
        if not self._custom_poi_options:
            return ""
        return self._custom_poi_options[
            self._current_poi_type_index
        ]["value"]

    def selectPage(self, index: int) -> None:
        root = self.qml_view.rootObject()
        if root is not None and 0 <= int(index) < 4:
            root.setProperty("currentPage", int(index))
