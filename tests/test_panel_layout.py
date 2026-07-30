"""Control-center layout smoke tests."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from huntoverlay.i18n import get_language, set_language
from huntoverlay.widgets.panel import (
    Panel,
    TacticalComboBox,
    TacticalDoubleSpinBox,
    centered_window_position,
)


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
        "1",
        False,
        False,
        False,
    )
    try:
        yield widget
    finally:
        widget.deleteLater()
        set_language(previous_language)


@pytest.mark.unit
def test_panel_uses_control_center_shell(panel):
    assert panel.findChild(QtWidgets.QTabWidget) is None
    assert panel.page_stack.count() == 4
    assert [button.text() for button in panel.nav_buttons] == [
        "地图与工具",
        "官方点位",
        "首领资料",
        "设置",
    ]
    assert all(not button.icon().isNull() for button in panel.nav_buttons)
    assert panel.page_stack.currentWidget() is panel.map_page
    assert panel.nav_buttons[0].isChecked() is True


@pytest.mark.unit
def test_navigation_switches_the_visible_page(panel):
    panel.nav_buttons[2].click()

    assert panel.page_stack.currentWidget() is panel.bosses_page
    assert panel.nav_buttons[2].isChecked() is True
    assert panel.page_title_label.text() == "首领资料"


@pytest.mark.unit
def test_map_page_keeps_high_frequency_controls_together(panel):
    for control in (
        panel.cmb,
        panel.scale_box,
        panel.chk_nums,
        panel.btn_add_poi,
        panel.btn_manage_pois,
        panel.btn_ruler,
        panel.btn_clear_rulers,
    ):
        assert panel.map_page.isAncestorOf(control)


@pytest.mark.unit
def test_platform_independent_input_arrows_are_kept(panel):
    assert isinstance(panel.cmb, TacticalComboBox)
    assert isinstance(panel.cmb_poi_type, TacticalComboBox)
    assert isinstance(panel.cmb_lang, TacticalComboBox)
    assert isinstance(panel.scale_box, TacticalDoubleSpinBox)


@pytest.mark.unit
def test_settings_page_keeps_recovery_controls_separate(panel):
    assert panel.chk_show_tray_icon.text() == "显示通知区域图标"
    assert panel.chk_minimize_to_tray.text() == "最小化面板到通知区域"
    assert panel.chk_start_hidden_to_tray.text() == "启动时隐藏到通知区域"
    for control in (
        panel.chk_show_tray_icon,
        panel.chk_minimize_to_tray,
        panel.chk_start_hidden_to_tray,
    ):
        assert panel.settings_page.isAncestorOf(control)


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
