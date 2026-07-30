"""QML control-center shell and bridge contract tests."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

import pytest
from PySide6 import QtCore, QtGui, QtQuickWidgets, QtWidgets

from huntoverlay.i18n import get_language, set_language
from huntoverlay.widgets.panel import Panel, centered_window_position


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


@pytest.fixture
def panel(qapp):
    previous_language = get_language()
    set_language("zh")
    specs = {
        "possible_xp": {
            "label": "潜在经验点",
            "default_fill": QtGui.QColor("#ffffff"),
            "border": QtGui.QColor("#111111"),
        },
        "spawns": {
            "label": "出生点",
            "default_fill": QtGui.QColor("#00ff00"),
            "border": QtGui.QColor("#111111"),
        },
        "armories": {
            "label": "军械库",
            "default_fill": QtGui.QColor("#ff0000"),
            "border": QtGui.QColor("#111111"),
        },
    }
    widget = Panel(
        ["possible_xp", "spawns", "armories"],
        specs,
        1.0,
        {"toggle_master": "总开关"},
        {"toggle_master": "F1"},
        "16:9",
        "1.2.0",
        False,
        False,
        False,
    )
    qapp.processEvents()
    try:
        yield widget
    finally:
        widget.qml_view.setSource(QtCore.QUrl())
        widget.close()
        widget.deleteLater()
        qapp.processEvents()
        set_language(previous_language)


@pytest.mark.unit
def test_panel_loads_qml_control_center_shell(panel):
    assert isinstance(panel.qml_view, QtQuickWidgets.QQuickWidget)
    assert panel.qml_view.status() == QtQuickWidgets.QQuickWidget.Ready
    assert panel.qml_view.errors() == []

    root = panel.qml_view.rootObject()
    assert root is not None
    assert root.objectName() == "controlCenterRoot"
    assert root.property("pageCount") == 4
    assert root.property("currentPage") == 0
    assert panel.uiText("Map & Tools") == "地图与工具"


@pytest.mark.unit
def test_navigation_switches_the_visible_qml_page(panel):
    panel.selectPage(2)

    assert panel.qml_view.rootObject().property("currentPage") == 2


@pytest.mark.unit
def test_map_page_exposes_high_frequency_controls(panel):
    root = panel.qml_view.rootObject()

    assert root.findChild(QtCore.QObject, "mapSelector") is not None
    assert root.findChild(QtCore.QObject, "numberSwitch") is not None
    assert root.findChild(QtCore.QObject, "userPoisSwitch") is not None
    assert root.findChild(QtCore.QObject, "customPoiSelector") is not None
    assert root.findChild(QtCore.QObject, "refreshButton") is not None


@pytest.mark.unit
def test_bridge_models_keep_runtime_values(panel):
    assert [item["value"] for item in panel.mapOptions] == [
        "Stillwater Bayou",
        "Lawson Delta",
        "DeSalle",
        "Mammon's Gulch",
    ]
    assert [item["value"] for item in panel.customPoiOptions] == [
        "spawns",
        "armories",
    ]
    assert panel.currentPoiType() == "spawns"
    assert panel.typeCount == 3
    assert panel.keybindItems == [
        {
            "action": "toggle_master",
            "label": "总开关",
            "value": "F1",
        }
    ]


@pytest.mark.unit
def test_external_setters_update_qml_state_without_user_signals(panel):
    emitted = []
    panel.mapSel.connect(lambda value: emitted.append(("map", value)))
    panel.scaleChanged.connect(
        lambda value: emitted.append(("scale", value))
    )
    panel.trayIconChanged.connect(
        lambda value: emitted.append(("tray", value))
    )

    panel.setMap("Lawson Delta")
    panel.setScale(1.25)
    panel.setTrayIconEnabled(True)
    panel.setCustomPoiCounts(3, 12)
    panel.setKeybindLabel("toggle_master", "Ctrl+F1")

    assert emitted == []
    assert panel.currentMapIndex == 1
    assert panel.currentMapLabel == "劳森三角洲"
    assert panel.scaleValue == pytest.approx(1.25)
    assert panel.trayIconEnabled is True
    assert panel.customPoiCountText == "当前分类： 3  |  全部自定义： 12"
    assert panel.keybindItems[0]["value"] == "Ctrl+F1"


@pytest.mark.unit
def test_ui_slots_emit_existing_panel_contract(panel):
    emitted = []
    panel.mapSel.connect(lambda value: emitted.append(("map", value)))
    panel.scaleChanged.connect(
        lambda value: emitted.append(("scale", value))
    )
    panel.tnums.connect(lambda value: emitted.append(("nums", value)))
    panel.typeToggled.connect(
        lambda key, value: emitted.append(("type", key, value))
    )

    panel.selectMap(1)
    panel.adjustScale(0.05)
    panel.setNumberSwitchFromUi(True)
    panel.setTypeEnabledFromUi("spawns", True)

    assert emitted == [
        ("map", "Lawson Delta"),
        ("scale", pytest.approx(1.05)),
        ("nums", True),
        ("type", "spawns", True),
    ]


@pytest.mark.unit
def test_type_state_and_settings_remain_separate(panel):
    panel.setTypeState("spawns", True, QtGui.QColor("#123456"))
    panel.setUserPoisEnabled(False)
    panel.setMinimizeToTrayEnabled(True)
    panel.setStartHiddenToTrayEnabled(True)
    panel.setHoldTabModeEnabled(True)
    panel.setBlockShiftTabEnabled(True)
    panel.setPanelFollowTabEnabled(True)

    spawns = next(
        item for item in panel.typeItems if item["key"] == "spawns"
    )
    assert spawns["enabled"] is True
    assert spawns["fill"] == "#123456"
    assert panel.userPoisEnabled is False
    assert panel.minimizeToTrayEnabled is True
    assert panel.startHiddenToTrayEnabled is True
    assert panel.holdTabModeEnabled is True
    assert panel.blockShiftTabEnabled is True
    assert panel.panelFollowTabEnabled is True


@pytest.mark.unit
def test_panel_is_landscape_and_resizable(panel):
    assert panel.minimumSize() == QtCore.QSize(760, 480)
    assert panel.size() == QtCore.QSize(1040, 660)
    assert panel.minimumWidth() < panel.maximumWidth()
    assert panel.minimumHeight() < panel.maximumHeight()
    assert panel.width() > panel.height()


@pytest.mark.unit
def test_centered_window_position_uses_available_screen_geometry():
    available = QtCore.QRect(100, 50, 1200, 800)

    position = centered_window_position(
        available,
        QtCore.QSize(1040, 660),
        margin=24,
    )

    assert position == QtCore.QPoint(180, 120)


@pytest.mark.unit
def test_centered_window_position_clamps_oversized_window_to_margin():
    available = QtCore.QRect(100, 50, 1000, 700)

    position = centered_window_position(
        available,
        QtCore.QSize(1200, 900),
        margin=24,
    )

    assert position == QtCore.QPoint(124, 74)
