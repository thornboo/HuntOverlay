"""Control panel window (Qt).

Verbatim move of the Panel class from the original single-file build.
Only imports changed: constants from huntoverlay.constants, key() from
huntoverlay.win32, DotChip from the sibling dialogs module.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from ..constants import APP_TITLE, MAPS, map_display
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
    forceRefresh = QtCore.Signal()


    def __init__(self, type_order, type_specs, start_scale: float, binds_label_map: dict, binds_current: dict, aspect: str, config_version: str, start_min_to_tray: bool, start_hold_tab_mode: bool, start_block_shift_tab: bool, p=None):
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
        btn_all = QtWidgets.QPushButton("全选")
        btn_none = QtWidgets.QPushButton("全不选")
        btn_all.clicked.connect(lambda: self._set_all_types(True))
        btn_none.clicked.connect(lambda: self._set_all_types(False))
        sel_row.addWidget(btn_all)
        sel_row.addWidget(btn_none)
        tv.addLayout(sel_row)

        map_row = QtWidgets.QHBoxLayout()
        map_row.addWidget(QtWidgets.QLabel("地图："))
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

        self.chk_nums = QtWidgets.QCheckBox("1-4 数字键切图")
        tv.addWidget(self.chk_nums)
        self.chk_nums.toggled.connect(self.tnums)

        tv.addSpacing(6)

        scale_row = QtWidgets.QHBoxLayout()
        scale_row.addWidget(QtWidgets.QLabel("缩放："))
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
        self.btn_def_colors = QtWidgets.QPushButton("重置颜色")
        tv.addWidget(self.btn_def_colors)
        self.btn_def_colors.clicked.connect(self.resetColors)

        tv.addStretch(1)
        tabs.addTab(types_page, "点位")

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
            btn = QtWidgets.QPushButton("设置")
            btn.setFixedWidth(48)
            row.addWidget(btn)
            kv.addLayout(row)
            self.kb_rows[action] = (btn, cur_lbl)
            btn.clicked.connect(lambda _, a=action: self.requestBindEdit.emit(a))

        kv.addStretch(1)
        tabs.addTab(kb_page, "快捷键")

        # ── Tab 3: Settings ───────────────────────────────────────────
        cfg_page = QtWidgets.QWidget()
        cv = QtWidgets.QVBoxLayout(cfg_page)
        cv.setContentsMargins(8, 8, 8, 8)
        cv.setSpacing(6)

        self.chk_tray = QtWidgets.QCheckBox("最小化到系统托盘")
        self.chk_tray.setChecked(bool(start_min_to_tray))
        cv.addWidget(self.chk_tray)
        self.chk_tray.toggled.connect(lambda b: self.minimizeToTrayChanged.emit(bool(b)))

        self.chk_hold_tab = QtWidgets.QCheckBox("按住 Tab 显示覆盖层")
        self.chk_hold_tab.setChecked(bool(start_hold_tab_mode))
        cv.addWidget(self.chk_hold_tab)
        self.chk_hold_tab.toggled.connect(lambda b: self.holdTabModeChanged.emit(bool(b)))

        self.chk_block_shift_tab = QtWidgets.QCheckBox("屏蔽 Shift+Tab")
        self.chk_block_shift_tab.setChecked(bool(start_block_shift_tab))
        cv.addWidget(self.chk_block_shift_tab)
        self.chk_block_shift_tab.toggled.connect(lambda b: self.blockShiftTabChanged.emit(bool(b)))

        cv.addSpacing(4)
        self.btn_reset_cfg = QtWidgets.QPushButton("恢复默认配置")
        cv.addWidget(self.btn_reset_cfg)
        self.btn_reset_cfg.clicked.connect(self.resetConfig)

        cv.addSpacing(8)

        update_row = QtWidgets.QHBoxLayout()
        self.update_label = QtWidgets.QLabel("数据：检查中...")
        self.update_label.setStyleSheet("color:#666666;font-size:11px;")
        update_row.addWidget(self.update_label)
        update_row.addStretch(1)
        self.btn_force_refresh = QtWidgets.QPushButton("刷新数据")
        self.btn_force_refresh.setFixedWidth(92)
        update_row.addWidget(self.btn_force_refresh)
        cv.addLayout(update_row)
        self.btn_force_refresh.clicked.connect(self.forceRefresh)

        cv.addSpacing(2)
        info_style = "color:#555555;font-size:11px;"
        lbl_info = QtWidgets.QLabel(f"屏幕比例：{aspect}  |  v{config_version}")
        lbl_info.setStyleSheet(info_style)
        cv.addWidget(lbl_info)
        lbl_path = QtWidgets.QLabel("%LOCALAPPDATA%\\HuntOverlay")
        lbl_path.setStyleSheet(info_style)
        cv.addWidget(lbl_path)

        cv.addStretch(1)
        tabs.addTab(cfg_page, "设置")

    def _dec_scale(self):
        self.scale_box.setValue(max(self.scale_box.minimum(), self.scale_box.value() - 0.05))

    def _inc_scale(self):
        self.scale_box.setValue(min(self.scale_box.maximum(), self.scale_box.value() + 0.05))

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

