"""Resizable control-center window for HuntOverlay."""

from PySide6 import QtCore, QtGui, QtWidgets

from .. import boss_data
from ..constants import APP_TITLE, MAPS
from ..i18n import available_languages, get_language, map_display, tr
from .dialogs import DotChip


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


class TacticalFrame(QtWidgets.QFrame):
    """A lightweight inner-edge and texture layer for panel surfaces."""

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        surface = self.property("tacticalSurface")
        if not surface:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setClipRect(self.rect())
        if surface in {"sidebar", "header"}:
            painter.setPen(QtGui.QPen(QtGui.QColor(220, 194, 150, 8), 1))
            height = self.height()
            for x in range(-height, self.width(), 48):
                painter.drawLine(x, 0, x + height, height)

        if surface != "sidebar":
            painter.setPen(QtGui.QPen(QtGui.QColor(232, 185, 103, 68), 1))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRoundedRect(
                QtCore.QRectF(self.rect()).adjusted(2.5, 2.5, -3.5, -3.5),
                4,
                4,
            )
        painter.end()


class TacticalComboBox(QtWidgets.QComboBox):
    """Combo box with a style-independent down-arrow glyph."""

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(
            QtGui.QColor("#D8C6A8" if self.isEnabled() else "#6F6B65")
        )
        center_x = self.width() - 14
        center_y = self.height() / 2 + 1
        painter.drawPolygon(
            QtGui.QPolygonF(
                [
                    QtCore.QPointF(center_x - 4.5, center_y - 2.5),
                    QtCore.QPointF(center_x + 4.5, center_y - 2.5),
                    QtCore.QPointF(center_x, center_y + 2.5),
                ]
            )
        )
        painter.end()


class TacticalDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    """Double spin box with style-independent step arrows."""

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(
            QtGui.QColor("#D8C6A8" if self.isEnabled() else "#6F6B65")
        )
        center_x = self.width() - 9
        upper_y = self.height() * 0.28
        lower_y = self.height() * 0.72
        painter.drawPolygon(
            QtGui.QPolygonF(
                [
                    QtCore.QPointF(center_x - 3.5, upper_y + 2),
                    QtCore.QPointF(center_x + 3.5, upper_y + 2),
                    QtCore.QPointF(center_x, upper_y - 2),
                ]
            )
        )
        painter.drawPolygon(
            QtGui.QPolygonF(
                [
                    QtCore.QPointF(center_x - 3.5, lower_y - 2),
                    QtCore.QPointF(center_x + 3.5, lower_y - 2),
                    QtCore.QPointF(center_x, lower_y + 2),
                ]
            )
        )
        painter.end()


class Panel(QtWidgets.QWidget):
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
        super().__init__(p, QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setObjectName("controlCenter")
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(self.MINIMUM_SIZE)
        self.resize(self.DEFAULT_SIZE)
        self.setStyleSheet(self._control_center_stylesheet())

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = TacticalFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setProperty("tacticalSurface", "sidebar")
        sidebar.setFixedWidth(226)
        side = QtWidgets.QVBoxLayout(sidebar)
        side.setContentsMargins(18, 22, 18, 18)
        side.setSpacing(9)

        brand = QtWidgets.QLabel("HuntOverlay")
        brand.setProperty("role", "brand")
        side.addWidget(brand)
        control_center = QtWidgets.QLabel(tr("Control Center"))
        control_center.setProperty("role", "brandSubtitle")
        side.addWidget(control_center)
        side.addSpacing(16)

        self.page_stack = QtWidgets.QStackedWidget()
        self.page_stack.setObjectName("pageStack")
        self.map_page = self._build_map_page(
            type_order,
            type_specs,
            start_scale,
            start_show_user_pois,
        )
        self.pois_page = self._build_pois_page(type_order, type_specs)
        self.bosses_page = self._build_boss_page()
        self.settings_page = self._build_settings_page(
            binds_label_map,
            binds_current,
            aspect,
            config_version,
            start_min_to_tray,
            start_hold_tab_mode,
            start_block_shift_tab,
            start_panel_follow_tab,
            start_show_tray_icon,
            start_start_hidden_to_tray,
        )
        pages = [
            (
                tr("Map & Tools"),
                tr("Map controls, custom POIs and measurement."),
                self.map_page,
            ),
            (
                tr("Official POIs"),
                tr("Visibility and marker colors for official data."),
                self.pois_page,
            ),
            (
                tr("Boss Reference"),
                tr("Combat resistances and practical notes."),
                self.bosses_page,
            ),
            (
                tr("Settings"),
                tr("Keybinds, overlay behavior and application recovery."),
                self.settings_page,
            ),
        ]

        self.nav_buttons = []
        self.nav_group = QtWidgets.QButtonGroup(self)
        self.nav_group.setExclusive(True)
        nav_icons = ("map", "poi", "boss", "settings")
        for index, (title, _description, page) in enumerate(pages):
            button = QtWidgets.QPushButton(title)
            button.setIcon(self._navigation_icon(nav_icons[index]))
            button.setIconSize(QtCore.QSize(32, 32))
            button.setProperty("nav", True)
            button.setCheckable(True)
            button.setCursor(QtCore.Qt.PointingHandCursor)
            button.setFocusPolicy(QtCore.Qt.StrongFocus)
            button.setAccessibleName(title)
            button.clicked.connect(
                lambda _checked=False, page_index=index: self._switch_page(
                    page_index
                )
            )
            self.nav_group.addButton(button, index)
            self.nav_buttons.append(button)
            side.addWidget(button)
            self.page_stack.addWidget(page)

        side.addStretch(1)
        status = TacticalFrame()
        status.setObjectName("statusCard")
        status.setProperty("tacticalSurface", "card")
        status_layout = QtWidgets.QVBoxLayout(status)
        status_layout.setContentsMargins(12, 12, 12, 12)
        status_layout.setSpacing(7)
        status_title = QtWidgets.QLabel(tr("Data Status"))
        status_title.setProperty("role", "sectionTitle")
        status_layout.addWidget(status_title)
        self.update_label = QtWidgets.QLabel(tr("Data: checking..."))
        self.update_label.setProperty("role", "status")
        self.update_label.setWordWrap(True)
        status_layout.addWidget(self.update_label)
        self.btn_force_refresh = QtWidgets.QPushButton(tr("Refresh Data"))
        self.btn_force_refresh.setAccessibleName(tr("Refresh Data"))
        self.btn_force_refresh.clicked.connect(self.forceRefresh)
        status_layout.addWidget(self.btn_force_refresh)
        side.addWidget(status)

        main = QtWidgets.QWidget()
        main.setObjectName("mainSurface")
        main_layout = QtWidgets.QVBoxLayout(main)
        main_layout.setContentsMargins(20, 16, 20, 20)
        main_layout.setSpacing(14)

        header_frame = TacticalFrame()
        header_frame.setObjectName("contentHeader")
        header_frame.setProperty("tacticalSurface", "header")
        header = QtWidgets.QHBoxLayout(header_frame)
        header.setContentsMargins(16, 11, 14, 11)
        header.setSpacing(12)
        heading = QtWidgets.QVBoxLayout()
        heading.setSpacing(2)
        self.page_title_label = QtWidgets.QLabel()
        self.page_title_label.setProperty("role", "pageTitle")
        heading.addWidget(self.page_title_label)
        self.page_description_label = QtWidgets.QLabel()
        self.page_description_label.setProperty("role", "pageDescription")
        heading.addWidget(self.page_description_label)
        header.addLayout(heading, 1)
        header_status_dot = QtWidgets.QLabel("●")
        header_status_dot.setProperty("role", "statusDot")
        header.addWidget(header_status_dot)
        self.header_update_label = QtWidgets.QLabel(
            tr("Data: checking...")
        )
        self.header_update_label.setProperty("role", "status")
        header.addWidget(self.header_update_label)
        header.addSpacing(4)
        version_label = QtWidgets.QLabel(f"v{config_version}")
        version_label.setProperty("role", "version")
        header.addWidget(version_label)
        header.addSpacing(4)
        self.current_map_badge = QtWidgets.QLabel(map_display(MAPS[0]))
        self.current_map_badge.setProperty("role", "badge")
        self.current_map_badge.setAlignment(QtCore.Qt.AlignCenter)
        header.addWidget(self.current_map_badge)
        self._apply_shadow(header_frame, blur_radius=14, y_offset=3)
        main_layout.addWidget(header_frame)
        main_layout.addWidget(self.page_stack, 1)

        root.addWidget(sidebar)
        root.addWidget(main, 1)

        self._page_titles = [
            (title, description) for title, description, _page in pages
        ]
        self._switch_page(0)

    @staticmethod
    def _control_center_stylesheet() -> str:
        return """
            QWidget#controlCenter {
                background: #0D0F10;
                color: #F1EADF;
                font-family: "Microsoft YaHei UI", "Segoe UI";
                font-size: 12px;
            }
            QFrame#sidebar {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #101214, stop:0.82 #151719, stop:1 #111315
                );
                border-right: 1px solid #5B4932;
            }
            QWidget#mainSurface, QStackedWidget#pageStack {
                background: #171A1D;
            }
            QWidget#scrollContent {
                background: #171A1D;
            }
            QFrame#contentHeader {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1C1D19, stop:0.65 #151719, stop:1 #101315
                );
                border: 2px solid #57482F;
                border-left: 4px solid #C99645;
                border-radius: 6px;
            }
            QLabel {
                color: #D7D0C5;
                background: transparent;
            }
            QLabel[role="brand"] {
                color: #F4E7D1;
                font-family: "Georgia", "Microsoft YaHei UI";
                font-size: 27px;
                font-weight: 700;
            }
            QLabel[role="brandSubtitle"] {
                color: #C99645;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel[role="pageTitle"] {
                color: #F4E7D8;
                font-family: "Bahnschrift SemiCondensed", "Microsoft YaHei UI";
                font-size: 26px;
                font-weight: 700;
            }
            QLabel[role="pageDescription"] {
                color: #8F969D;
                font-size: 12px;
            }
            QLabel[role="sectionTitle"] {
                color: #E1BC75;
                font-size: 17px;
                font-weight: 700;
            }
            QLabel[role="cardMarker"] {
                color: #C99945;
                font-size: 23px;
                font-weight: 700;
                min-width: 28px;
            }
            QLabel[role="sectionDescription"], QLabel[role="muted"] {
                color: #8F969D;
                font-size: 11px;
            }
            QLabel[role="status"] {
                color: #8FC59A;
                font-size: 12px;
            }
            QLabel[role="statusDot"] {
                color: #77C786;
                font-size: 15px;
            }
            QLabel[role="version"] {
                color: #A6A9A7;
                font-size: 12px;
            }
            QLabel[role="badge"] {
                color: #F0CE8C;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #303238, stop:1 #22262A
                );
                border: 1px solid #665338;
                border-radius: 5px;
                padding: 8px 14px;
                font-weight: 700;
            }
            QFrame[card="true"], QFrame#statusCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #282B2C, stop:0.08 #242829, stop:1 #1B1F21
                );
                border: 1px solid #6A573B;
                border-radius: 6px;
            }
            QFrame[poiItem="true"] {
                background: #1D2123;
                border: 1px solid #3D3933;
                border-radius: 4px;
            }
            QFrame#cardDivider {
                background: #594832;
                border: 0;
                max-height: 1px;
            }
            QPushButton {
                min-height: 36px;
                color: #F0E7DA;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3A3D40, stop:0.1 #34373A,
                    stop:0.86 #25292C, stop:1 #1C2023
                );
                border: 1px solid #625744;
                border-radius: 4px;
                padding: 2px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45474A, stop:1 #2C3033
                );
                border-color: #A17D47;
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1A1E21, stop:1 #2B2E31
                );
                padding-top: 4px;
            }
            QPushButton:focus, QComboBox:focus, QSpinBox:focus,
            QDoubleSpinBox:focus {
                border: 1px solid #F0BD62;
            }
            QPushButton:disabled {
                color: #626970;
                background: #202428;
            }
            QPushButton[nav="true"] {
                min-height: 56px;
                color: #B9B0A3;
                background: transparent;
                border: 1px solid transparent;
                border-left: 4px solid transparent;
                border-radius: 4px;
                text-align: left;
                padding: 0 15px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton[nav="true"]:hover {
                color: #F1EADF;
                background: #202429;
                border-color: #2E3439;
            }
            QPushButton[nav="true"]:checked {
                color: #EDC67A;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #302B1E, stop:0.78 #28271F, stop:1 #211F1A
                );
                border: 1px solid #765B31;
                border-left: 4px solid #C99945;
                font-weight: 700;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                min-height: 36px;
                color: #F1EADF;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #111416, stop:0.9 #181B1D, stop:1 #26292B
                );
                border: 1px solid #665A47;
                border-radius: 4px;
                padding: 0 8px;
                selection-background-color: #6B532E;
                font-size: 12px;
            }
            QComboBox::drop-down {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34373A, stop:1 #202427
                );
                border: 0;
                border-left: 1px solid #665A47;
                width: 28px;
            }
            QComboBox::down-arrow,
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow,
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                width: 0;
                height: 0;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #393C3F, stop:1 #202427
                );
                border-left: 1px solid #665A47;
                width: 18px;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                border-bottom: 1px solid #413A30;
                border-top-right-radius: 3px;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                border-bottom-right-radius: 3px;
            }
            QAbstractItemView {
                color: #F1EADF;
                background: #1B1F23;
                border: 1px solid #414951;
                selection-background-color: #6B532E;
                outline: 0;
            }
            QCheckBox {
                color: #D7D0C5;
                spacing: 8px;
                min-height: 28px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QScrollArea {
                background: #171A1D;
                border: 0;
            }
            QAbstractScrollArea::viewport {
                background: #171A1D;
            }
            QScrollBar:vertical {
                background: #1A1E21;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #495057;
                min-height: 24px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
        """

    @staticmethod
    def _navigation_icon(kind: str, size: int = 24) -> QtGui.QIcon:
        """Draw a compact brass navigation icon without external assets."""
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor("#C99945"), 2.0)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)

        if kind == "map":
            for x, y in ((4, 4), (13, 4), (4, 13), (13, 13)):
                painter.drawRoundedRect(QtCore.QRectF(x, y, 7, 7), 1.2, 1.2)
        elif kind == "poi":
            painter.drawEllipse(QtCore.QPointF(12, 11), 6.5, 6.5)
            painter.drawEllipse(QtCore.QPointF(12, 11), 1.7, 1.7)
            painter.drawLine(QtCore.QPointF(12, 2), QtCore.QPointF(12, 5))
            painter.drawLine(QtCore.QPointF(3, 11), QtCore.QPointF(6, 11))
            painter.drawLine(QtCore.QPointF(18, 11), QtCore.QPointF(21, 11))
            painter.drawLine(QtCore.QPointF(12, 17.5), QtCore.QPointF(12, 22))
        elif kind == "boss":
            shield = QtGui.QPainterPath()
            shield.moveTo(12, 3)
            shield.lineTo(19, 6)
            shield.lineTo(18, 14)
            shield.cubicTo(17, 18, 14.5, 20.5, 12, 22)
            shield.cubicTo(9.5, 20.5, 7, 18, 6, 14)
            shield.lineTo(5, 6)
            shield.closeSubpath()
            painter.drawPath(shield)
            painter.drawLine(QtCore.QPointF(9, 8), QtCore.QPointF(15, 14))
            painter.drawLine(QtCore.QPointF(15, 8), QtCore.QPointF(9, 14))
        else:
            painter.drawEllipse(QtCore.QPointF(12, 12), 6.5, 6.5)
            painter.drawEllipse(QtCore.QPointF(12, 12), 2.2, 2.2)
            for start, end in (
                ((12, 2), (12, 5)),
                ((12, 19), (12, 22)),
                ((2, 12), (5, 12)),
                ((19, 12), (22, 12)),
                ((5, 5), (7, 7)),
                ((17, 17), (19, 19)),
                ((19, 5), (17, 7)),
                ((5, 19), (7, 17)),
            ):
                painter.drawLine(
                    QtCore.QPointF(*start),
                    QtCore.QPointF(*end),
                )
        painter.end()
        return QtGui.QIcon(pixmap)

    @staticmethod
    def _apply_shadow(
        widget: QtWidgets.QWidget,
        blur_radius: int = 12,
        y_offset: int = 3,
    ) -> None:
        shadow = QtWidgets.QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(0, y_offset)
        shadow.setColor(QtGui.QColor(0, 0, 0, 105))
        widget.setGraphicsEffect(shadow)

    def _make_card(
        self,
        title: str,
        description: str = "",
        marker: str = "",
    ):
        card = TacticalFrame()
        card.setProperty("card", True)
        card.setProperty("tacticalSurface", "card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(10)
        title_row = QtWidgets.QHBoxLayout()
        title_row.setSpacing(8)
        if marker:
            marker_label = QtWidgets.QLabel(marker)
            marker_label.setProperty("role", "cardMarker")
            marker_label.setAlignment(
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            )
            title_row.addWidget(marker_label)
        title_label = QtWidgets.QLabel(tr(title))
        title_label.setProperty("role", "sectionTitle")
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        layout.addLayout(title_row)
        if description:
            description_label = QtWidgets.QLabel(tr(description))
            description_label.setProperty("role", "sectionDescription")
            description_label.setWordWrap(True)
            layout.addWidget(description_label)
        divider = QtWidgets.QFrame()
        divider.setObjectName("cardDivider")
        divider.setFrameShape(QtWidgets.QFrame.HLine)
        layout.addWidget(divider)
        self._apply_shadow(card)
        return card, layout

    def _build_map_page(
        self,
        type_order,
        type_specs,
        start_scale: float,
        start_show_user_pois: bool,
    ):
        page = QtWidgets.QWidget()
        page.setObjectName("mapPage")
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        inner = QtWidgets.QWidget()
        inner.setObjectName("scrollContent")
        grid = QtWidgets.QGridLayout(inner)
        grid.setContentsMargins(0, 0, 4, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        map_card, map_layout = self._make_card(
            "Map Controls",
            "Choose the active map and marker scale.",
            "▦",
        )
        map_row = QtWidgets.QHBoxLayout()
        map_row.addWidget(QtWidgets.QLabel(tr("Map:")))
        self.cmb = TacticalComboBox()
        for map_name in MAPS:
            self.cmb.addItem(map_display(map_name), map_name)
        map_row.addWidget(self.cmb, 1)
        map_layout.addLayout(map_row)
        self.cmb.currentIndexChanged.connect(self._map_changed)

        scale_row = QtWidgets.QHBoxLayout()
        scale_row.addWidget(QtWidgets.QLabel(tr("Scale:")))
        scale_row.addStretch(1)
        self.btn_dec = QtWidgets.QPushButton("−")
        self.btn_dec.setFixedWidth(34)
        self.btn_dec.setAccessibleName(tr("Decrease marker scale"))
        self.btn_inc = QtWidgets.QPushButton("+")
        self.btn_inc.setFixedWidth(34)
        self.btn_inc.setAccessibleName(tr("Increase marker scale"))
        self.scale_box = TacticalDoubleSpinBox()
        self.scale_box.setRange(0.10, 5.00)
        self.scale_box.setDecimals(2)
        self.scale_box.setSingleStep(0.05)
        self.scale_box.setValue(float(start_scale))
        self.scale_box.setFixedWidth(78)
        scale_row.addWidget(self.btn_dec)
        scale_row.addWidget(self.btn_inc)
        scale_row.addWidget(self.scale_box)
        map_layout.addLayout(scale_row)
        self.btn_dec.clicked.connect(self._dec_scale)
        self.btn_inc.clicked.connect(self._inc_scale)
        self.scale_box.valueChanged.connect(
            lambda value: self.scaleChanged.emit(float(value))
        )

        self.chk_nums = QtWidgets.QCheckBox(tr("1-4 map switch keys"))
        self.chk_nums.toggled.connect(self.tnums)
        map_layout.addWidget(self.chk_nums)
        map_layout.addStretch(1)

        official_card, official_layout = self._make_card(
            "Official Visibility",
            "Show or hide the complete official POI layer.",
            "⌖",
        )
        official_summary = QtWidgets.QLabel(
            tr("Official categories available: {count}").format(
                count=len(type_order)
            )
        )
        official_summary.setProperty("role", "status")
        official_layout.addWidget(official_summary)
        official_actions = QtWidgets.QHBoxLayout()
        self.btn_show_all_pois = QtWidgets.QPushButton(tr("Show All POIs"))
        self.btn_hide_all_pois = QtWidgets.QPushButton(tr("Hide All POIs"))
        self.btn_show_all_pois.clicked.connect(
            lambda: self._set_all_types(True)
        )
        self.btn_hide_all_pois.clicked.connect(
            lambda: self._set_all_types(False)
        )
        official_actions.addWidget(self.btn_show_all_pois)
        official_actions.addWidget(self.btn_hide_all_pois)
        official_layout.addLayout(official_actions)
        official_layout.addStretch(1)

        custom_card, custom_layout = self._make_card(
            "Custom POIs",
            "Create local markers without changing official data.",
            "⚑",
        )
        self.chk_user_pois = QtWidgets.QCheckBox(tr("Show custom POIs"))
        self.chk_user_pois.setChecked(bool(start_show_user_pois))
        self.chk_user_pois.toggled.connect(
            lambda value: self.userPoisToggled.emit(bool(value))
        )
        custom_layout.addWidget(self.chk_user_pois)

        poi_type_row = QtWidgets.QHBoxLayout()
        poi_type_row.addWidget(QtWidgets.QLabel(tr("POI type:")))
        self.cmb_poi_type = TacticalComboBox()
        for type_key in type_order:
            if type_key == "possible_xp":
                continue
            self.cmb_poi_type.addItem(type_specs[type_key]["label"], type_key)
        poi_type_row.addWidget(self.cmb_poi_type, 1)
        custom_layout.addLayout(poi_type_row)
        self.cmb_poi_type.currentIndexChanged.connect(
            lambda _index: self.customPoiContextChanged.emit()
        )

        self.lbl_custom_counts = QtWidgets.QLabel("")
        self.lbl_custom_counts.setProperty("role", "muted")
        custom_layout.addWidget(self.lbl_custom_counts)
        poi_actions = QtWidgets.QHBoxLayout()
        self.btn_add_poi = QtWidgets.QPushButton(tr("Add from Map"))
        self.btn_manage_pois = QtWidgets.QPushButton(tr("Manage POIs"))
        self.btn_add_poi.clicked.connect(self._emit_poi_pick_request)
        self.btn_manage_pois.clicked.connect(self._emit_poi_editor_request)
        poi_actions.addWidget(self.btn_add_poi)
        poi_actions.addWidget(self.btn_manage_pois)
        custom_layout.addLayout(poi_actions)
        custom_layout.addStretch(1)

        tools_card, tools_layout = self._make_card(
            "Measurement",
            "Measure distances or clear stored rulers.",
            "⌁",
        )
        tool_hint = QtWidgets.QLabel(
            tr("Choose Ruler, then click two points on the map.")
        )
        tool_hint.setProperty("role", "muted")
        tool_hint.setWordWrap(True)
        tools_layout.addWidget(tool_hint)
        tool_actions = QtWidgets.QHBoxLayout()
        self.btn_ruler = QtWidgets.QPushButton(tr("Ruler"))
        self.btn_clear_rulers = QtWidgets.QPushButton(tr("Clear Rulers"))
        self.btn_ruler.clicked.connect(self.requestRuler)
        self.btn_clear_rulers.clicked.connect(self.requestClearRulers)
        tool_actions.addWidget(self.btn_ruler)
        tool_actions.addWidget(self.btn_clear_rulers)
        tools_layout.addLayout(tool_actions)
        tools_layout.addStretch(1)

        grid.addWidget(map_card, 0, 0)
        grid.addWidget(official_card, 0, 1)
        grid.addWidget(custom_card, 1, 0)
        grid.addWidget(tools_card, 1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    def _build_pois_page(self, type_order, type_specs):
        page = QtWidgets.QWidget()
        page.setObjectName("poisPage")
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        toolbar, toolbar_layout = self._make_card(
            "Official Filters",
            "Toggle categories and tune their marker colors.",
            "⌖",
        )
        actions = QtWidgets.QHBoxLayout()
        self.btn_select_all = QtWidgets.QPushButton(tr("Select All"))
        self.btn_deselect_all = QtWidgets.QPushButton(tr("Deselect All"))
        self.btn_def_colors = QtWidgets.QPushButton(tr("Reset Colors"))
        self.btn_select_all.clicked.connect(
            lambda: self._set_all_types(True)
        )
        self.btn_deselect_all.clicked.connect(
            lambda: self._set_all_types(False)
        )
        self.btn_def_colors.clicked.connect(self.resetColors)
        actions.addWidget(self.btn_select_all)
        actions.addWidget(self.btn_deselect_all)
        actions.addStretch(1)
        actions.addWidget(self.btn_def_colors)
        toolbar_layout.addLayout(actions)
        outer.addWidget(toolbar)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        inner = QtWidgets.QWidget()
        inner.setObjectName("scrollContent")
        grid = QtWidgets.QGridLayout(inner)
        grid.setContentsMargins(0, 0, 4, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.type_widgets = {}
        for index, type_key in enumerate(type_order):
            spec = type_specs[type_key]
            item = QtWidgets.QFrame()
            item.setProperty("poiItem", True)
            item_layout = QtWidgets.QHBoxLayout(item)
            item_layout.setContentsMargins(12, 8, 10, 8)
            item_layout.setSpacing(8)
            checkbox = QtWidgets.QCheckBox(spec["label"])
            chip = DotChip(spec["default_fill"], spec["border"])
            item_layout.addWidget(checkbox, 1)
            item_layout.addWidget(chip)
            self.type_widgets[type_key] = (checkbox, chip)
            checkbox.toggled.connect(
                lambda value, key=type_key: self.typeToggled.emit(key, value)
            )
            chip.changed.connect(
                lambda color, key=type_key: self.typeColor.emit(key, color)
            )
            grid.addWidget(item, index // 2, index % 2)

        grid.setRowStretch((len(type_order) + 1) // 2, 1)
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)
        return page

    def _build_settings_page(
        self,
        binds_label_map: dict,
        binds_current: dict,
        aspect: str,
        config_version: str,
        start_min_to_tray: bool,
        start_hold_tab_mode: bool,
        start_block_shift_tab: bool,
        start_panel_follow_tab: bool,
        start_show_tray_icon: bool,
        start_start_hidden_to_tray: bool,
    ):
        page = QtWidgets.QWidget()
        page.setObjectName("settingsPage")
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        inner = QtWidgets.QWidget()
        inner.setObjectName("scrollContent")
        grid = QtWidgets.QGridLayout(inner)
        grid.setContentsMargins(0, 0, 4, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        keybind_card, keybind_layout = self._make_card(
            "Keybinds",
            "Keep common overlay actions within easy reach.",
            "⌨",
        )
        self.kb_rows = {}
        for action, label in binds_label_map.items():
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label))
            row.addStretch(1)
            current = QtWidgets.QLabel(binds_current.get(action, ""))
            current.setProperty("role", "badge")
            current.setAlignment(QtCore.Qt.AlignCenter)
            row.addWidget(current)
            button = QtWidgets.QPushButton(tr("Set"))
            button.setFixedWidth(58)
            button.clicked.connect(
                lambda _checked=False, action_key=action:
                    self.requestBindEdit.emit(action_key)
            )
            row.addWidget(button)
            keybind_layout.addLayout(row)
            self.kb_rows[action] = (button, current)
        keybind_layout.addStretch(1)

        overlay_card, overlay_layout = self._make_card(
            "Overlay Behavior",
            "Choose how the overlay and control center appear during play.",
            "◫",
        )
        self.chk_hold_tab = QtWidgets.QCheckBox(
            tr("Hold Tab to show overlay")
        )
        self.chk_hold_tab.setChecked(bool(start_hold_tab_mode))
        self.chk_hold_tab.toggled.connect(
            lambda value: self.holdTabModeChanged.emit(bool(value))
        )
        overlay_layout.addWidget(self.chk_hold_tab)
        self.chk_panel_follow_tab = QtWidgets.QCheckBox(
            tr("Panel follows Tab (show/hide with overlay)")
        )
        self.chk_panel_follow_tab.setChecked(bool(start_panel_follow_tab))
        self.chk_panel_follow_tab.toggled.connect(
            lambda value: self.panelFollowTabChanged.emit(bool(value))
        )
        overlay_layout.addWidget(self.chk_panel_follow_tab)
        self.chk_block_shift_tab = QtWidgets.QCheckBox(
            tr("Block Shift+Tab")
        )
        self.chk_block_shift_tab.setChecked(bool(start_block_shift_tab))
        self.chk_block_shift_tab.toggled.connect(
            lambda value: self.blockShiftTabChanged.emit(bool(value))
        )
        overlay_layout.addWidget(self.chk_block_shift_tab)
        overlay_layout.addStretch(1)

        app_card, app_layout = self._make_card(
            "Application",
            "Language and notification-area behavior.",
            "⚙",
        )
        language_row = QtWidgets.QHBoxLayout()
        language_row.addWidget(QtWidgets.QLabel(tr("Language:")))
        self.cmb_lang = TacticalComboBox()
        for code, display in available_languages():
            self.cmb_lang.addItem(display, code)
        current_language = self.cmb_lang.findData(get_language())
        if current_language >= 0:
            self.cmb_lang.setCurrentIndex(current_language)
        language_row.addWidget(self.cmb_lang, 1)
        app_layout.addLayout(language_row)
        self.cmb_lang.currentIndexChanged.connect(
            lambda _index: self.languageChanged.emit(
                self.cmb_lang.currentData()
            )
        )
        self.lbl_lang_hint = QtWidgets.QLabel(
            tr("Restart to apply the language change.")
        )
        self.lbl_lang_hint.setProperty("role", "muted")
        self.lbl_lang_hint.setVisible(False)
        app_layout.addWidget(self.lbl_lang_hint)

        self.chk_show_tray_icon = QtWidgets.QCheckBox(
            tr("Show notification area icon")
        )
        self.chk_show_tray_icon.setChecked(bool(start_show_tray_icon))
        self.chk_show_tray_icon.toggled.connect(
            lambda value: self.trayIconChanged.emit(bool(value))
        )
        app_layout.addWidget(self.chk_show_tray_icon)
        self.chk_minimize_to_tray = QtWidgets.QCheckBox(
            tr("Minimize panel to notification area")
        )
        self.chk_minimize_to_tray.setChecked(bool(start_min_to_tray))
        self.chk_minimize_to_tray.toggled.connect(
            lambda value: self.minimizeToTrayChanged.emit(bool(value))
        )
        app_layout.addWidget(self.chk_minimize_to_tray)
        self.chk_start_hidden_to_tray = QtWidgets.QCheckBox(
            tr("Start hidden in notification area")
        )
        self.chk_start_hidden_to_tray.setChecked(
            bool(start_start_hidden_to_tray)
        )
        self.chk_start_hidden_to_tray.toggled.connect(
            lambda value: self.startHiddenToTrayChanged.emit(bool(value))
        )
        app_layout.addWidget(self.chk_start_hidden_to_tray)
        app_layout.addStretch(1)

        data_card, data_layout = self._make_card(
            "Data & Storage",
            "Inspect local storage or restore the default configuration.",
            "▣",
        )
        info = QtWidgets.QLabel(
            f"{tr('Aspect:')}{aspect}  ·  v{config_version}"
        )
        info.setProperty("role", "muted")
        data_layout.addWidget(info)
        path_label = QtWidgets.QLabel("%LOCALAPPDATA%\\HuntOverlay")
        path_label.setProperty("role", "muted")
        path_label.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
        )
        data_layout.addWidget(path_label)
        self.btn_open_data_dir = QtWidgets.QPushButton(
            tr("Open Data Folder")
        )
        self.btn_open_data_dir.clicked.connect(self.requestOpenDataDir)
        data_layout.addWidget(self.btn_open_data_dir)
        self.btn_reset_cfg = QtWidgets.QPushButton(
            tr("Reset to Default Config")
        )
        self.btn_reset_cfg.clicked.connect(self.resetConfig)
        data_layout.addWidget(self.btn_reset_cfg)
        data_layout.addStretch(1)

        grid.addWidget(keybind_card, 0, 0, 2, 1)
        grid.addWidget(overlay_card, 0, 1)
        grid.addWidget(app_card, 1, 1)
        grid.addWidget(data_card, 2, 0, 1, 2)
        grid.setRowStretch(3, 1)
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    def _build_boss_page(self):
        """Build the read-only boss reference as a two-column card grid."""
        page = QtWidgets.QWidget()
        page.setObjectName("bossesPage")
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        inner = QtWidgets.QWidget()
        inner.setObjectName("scrollContent")
        grid = QtWidgets.QGridLayout(inner)
        grid.setContentsMargins(0, 0, 4, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        resistance_colors = {
            boss_data.WEAK: "#7EE787",
            boss_data.IMMUNE: "#FF7B72",
            boss_data.NORMAL: "#9AA0A6",
        }
        resistance_labels = {
            boss_data.WEAK: tr("Weak"),
            boss_data.IMMUNE: tr("Immune"),
            boss_data.NORMAL: tr("Normal"),
        }

        card_index = 0
        for key in boss_data.boss_keys():
            boss = boss_data.get_boss(key)
            if not boss:
                continue
            card, card_layout = self._make_card(
                boss["name"],
                marker="♜",
            )
            resistance_row = QtWidgets.QHBoxLayout()
            resistance_row.setSpacing(14)
            for damage_key, damage_name in (
                ("fire", tr("Fire")),
                ("poison", tr("Poison")),
            ):
                value = boss.get(damage_key, boss_data.NORMAL)
                label = QtWidgets.QLabel(
                    f"{damage_name}: {resistance_labels[value]}"
                )
                label.setStyleSheet(
                    f"color:{resistance_colors[value]};font-weight:600;"
                )
                resistance_row.addWidget(label)
            resistance_row.addStretch(1)
            card_layout.addLayout(resistance_row)
            for tip in boss.get("tips", []):
                tip_label = QtWidgets.QLabel("• " + tr(tip))
                tip_label.setWordWrap(True)
                card_layout.addWidget(tip_label)
            card_layout.addStretch(1)
            grid.addWidget(card, card_index // 2, card_index % 2)
            card_index += 1

        note = QtWidgets.QLabel(
            tr("Banish time and exact HP vary by patch and are omitted.")
        )
        note.setProperty("role", "muted")
        note.setWordWrap(True)
        grid.addWidget(note, (card_index + 1) // 2, 0, 1, 2)
        grid.setRowStretch((card_index + 1) // 2 + 1, 1)
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    def _switch_page(self, index: int):
        if not (0 <= index < self.page_stack.count()):
            return
        self.page_stack.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)
        title, description = self._page_titles[index]
        self.page_title_label.setText(title)
        self.page_description_label.setText(description)

    def _map_changed(self, _index: int):
        map_name = self.cmb.currentData()
        self.current_map_badge.setText(map_display(map_name))
        self.mapSel.emit(str(map_name or ""))

    def _dec_scale(self):
        self.scale_box.setValue(
            max(
                self.scale_box.minimum(),
                self.scale_box.value() - 0.05,
            )
        )

    def _inc_scale(self):
        self.scale_box.setValue(
            min(
                self.scale_box.maximum(),
                self.scale_box.value() + 0.05,
            )
        )

    def _emit_poi_editor_request(self):
        category = self.cmb_poi_type.currentData()
        self.requestPoiEditor.emit(str(category or ""))

    def _emit_poi_pick_request(self):
        category = self.cmb_poi_type.currentData()
        self.requestPoiPick.emit(str(category or ""))

    def setTypeState(
        self,
        tkey: str,
        enabled: bool,
        fill_color: QtGui.QColor,
    ):
        checkbox, chip = self.type_widgets[tkey]
        checkbox.blockSignals(True)
        chip.blockSignals(True)
        checkbox.setChecked(bool(enabled))
        chip.setFill(fill_color)
        chip.blockSignals(False)
        checkbox.blockSignals(False)

    def _set_all_types(self, enabled: bool):
        """Check or uncheck every POI category."""
        for checkbox, _chip in self.type_widgets.values():
            checkbox.setChecked(bool(enabled))

    def setMap(self, name: str):
        index = self.cmb.findData(name)
        if index >= 0:
            self.cmb.blockSignals(True)
            self.cmb.setCurrentIndex(index)
            self.cmb.blockSignals(False)
            self.current_map_badge.setText(map_display(name))

    def setLastUpdateText(self, txt: str):
        self.update_label.setText(txt)
        self.header_update_label.setText(txt)

    def setCustomPoiCounts(self, current: int, total: int):
        self.lbl_custom_counts.setText(
            f"{tr('Current category:')} {int(current)}  |  "
            f"{tr('All custom:')} {int(total)}"
        )

    def setKeybindLabel(self, action: str, txt: str):
        entry = self.kb_rows.get(action)
        if entry:
            entry[1].setText(txt)
