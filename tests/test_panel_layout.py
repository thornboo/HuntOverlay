"""Panel layout smoke tests."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtGui, QtWidgets

from huntoverlay.i18n import get_language, set_language
from huntoverlay.widgets.panel import Panel


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


@pytest.mark.unit
def test_panel_keeps_high_frequency_controls_on_map_tab(qapp):
    previous_language = get_language()
    set_language("zh")
    try:
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
        panel = Panel(
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

        tabs = panel.findChild(QtWidgets.QTabWidget)

        assert [tabs.tabText(i) for i in range(tabs.count())] == [
            "地图",
            "点位",
            "设置",
            "首领",
        ]
        assert panel.btn_add_poi.parentWidget() is tabs.widget(0)
        assert panel.btn_ruler.parentWidget() is tabs.widget(0)
        assert panel.chk_show_tray_icon.text() == "显示通知区域图标"
        assert panel.chk_minimize_to_tray.text() == "最小化面板到通知区域"
        assert panel.chk_start_hidden_to_tray.text() == "启动时隐藏到通知区域"
    finally:
        set_language(previous_language)
