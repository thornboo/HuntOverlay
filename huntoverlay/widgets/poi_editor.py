"""POI editor dialog — add/remove user-authored points (Qt).

Edits only user points (data.json points are read-only). All mutation goes
through the tested huntoverlay.user_data pure functions; the dialog holds a
working copy and only the accepted result is read back by the overlay, so
cancelling changes nothing. No network access.
"""

import copy

from PySide6 import QtCore, QtGui, QtWidgets

from ..constants import MAPS
from ..i18n import map_display, category_label, tr
from .. import user_data
from .. import transfer


# POI categories the editor exposes (matches the overlay's render order,
# excluding the possible_xp union which is derived, not stored).
_EDITABLE_CATEGORIES = [
    "spawns", "armories", "towers", "big_towers", "workbenches",
    "wild_targets", "brutes", "beetles", "easter_eggs",
    "melee_weapons", "cash_registers",
]


class PoiEditorDialog(QtWidgets.QDialog):
    def __init__(self, user_pois: dict, icon: str = "", p=None,
                 init_map: str = "", init_cat: str = "",
                 prefill_xy=None):
        super().__init__(p)
        # Set to True (with pick_map/pick_cat recorded) when the user asks to
        # pick a coordinate from the map; the overlay reads these after exec().
        self.pick_requested = False
        self.pick_map = ""
        self.pick_cat = ""
        self.setWindowTitle(tr("Edit Custom POIs"))
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.resize(440, 420)
        if icon:
            self.setWindowIcon(QtGui.QIcon(icon))
        self.setStyleSheet(
            "QWidget{background:#1e1f22;color:#e6e6e6;font-size:12px;}"
            "QComboBox,QSpinBox,QLineEdit{background:#2b2d30;color:#e6e6e6;"
            "border:1px solid #3a3c40;padding:2px 4px;}"
            "QPushButton{background:#2b2d30;border:1px solid #3a3c40;padding:4px 10px;}"
            "QPushButton:hover{background:#34363a;}"
            "QTableWidget{background:#242629;gridline-color:#3a3c40;}"
            "QHeaderView::section{background:#2b2d30;color:#cfd1d4;border:0;padding:3px;}"
        )

        # Working copy — overlay reads result_pois only on accept, so cancel
        # (closing the window) leaves the overlay's data untouched.
        self.result_pois = copy.deepcopy(user_pois) if isinstance(user_pois, dict) \
            else user_data.empty_user_pois()
        self.result_pois.setdefault("version", 1)
        self.result_pois.setdefault("maps", {})

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Map + category selectors.
        sel = QtWidgets.QHBoxLayout()
        sel.addWidget(QtWidgets.QLabel(tr("Map:")))
        self.cmb_map = QtWidgets.QComboBox()
        for m in MAPS:
            self.cmb_map.addItem(map_display(m), m)
        sel.addWidget(self.cmb_map, 1)
        sel.addWidget(QtWidgets.QLabel(tr("Category:")))
        self.cmb_cat = QtWidgets.QComboBox()
        for c in _EDITABLE_CATEGORIES:
            self.cmb_cat.addItem(category_label(c, c), c)
        sel.addWidget(self.cmb_cat, 1)
        root.addLayout(sel)

        hint = QtWidgets.QLabel(tr("Custom points only (official points are read-only)"))
        hint.setStyleSheet("color:#8a8d93;")
        root.addWidget(hint)

        # Table of current user points.
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["X", "Y", tr("Description")])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        root.addWidget(self.table, 1)

        # Add row: X / Y / desc / +
        addr = QtWidgets.QHBoxLayout()
        self.sp_x = QtWidgets.QSpinBox()
        self.sp_x.setRange(user_data.COORD_MIN, user_data.COORD_MAX)
        self.sp_y = QtWidgets.QSpinBox()
        self.sp_y.setRange(user_data.COORD_MIN, user_data.COORD_MAX)
        self.ed_desc = QtWidgets.QLineEdit()
        self.ed_desc.setPlaceholderText(tr("Description"))
        addr.addWidget(QtWidgets.QLabel("X"))
        addr.addWidget(self.sp_x)
        addr.addWidget(QtWidgets.QLabel("Y"))
        addr.addWidget(self.sp_y)
        addr.addWidget(self.ed_desc, 1)
        btn_add = QtWidgets.QPushButton(tr("Add"))
        btn_add.clicked.connect(self._add_point)
        addr.addWidget(btn_add)
        btn_pick = QtWidgets.QPushButton(tr("Pick from Map"))
        btn_pick.clicked.connect(self._request_pick)
        addr.addWidget(btn_pick)
        root.addLayout(addr)

        # Bottom buttons.
        bot = QtWidgets.QHBoxLayout()
        btn_del = QtWidgets.QPushButton(tr("Delete Selected"))
        btn_del.clicked.connect(self._delete_selected)
        bot.addWidget(btn_del)
        btn_import = QtWidgets.QPushButton(tr("Import"))
        btn_import.clicked.connect(self._import)
        bot.addWidget(btn_import)
        btn_export = QtWidgets.QPushButton(tr("Export"))
        btn_export.clicked.connect(self._export)
        bot.addWidget(btn_export)
        bot.addStretch(1)
        btn_close = QtWidgets.QPushButton(tr("Close"))
        btn_close.clicked.connect(self.accept)
        bot.addWidget(btn_close)
        root.addLayout(bot)

        self.cmb_map.currentIndexChanged.connect(self._refresh_table)
        self.cmb_cat.currentIndexChanged.connect(self._refresh_table)

        # Restore context after returning from a map pick.
        if init_map:
            i = self.cmb_map.findData(init_map)
            if i >= 0:
                self.cmb_map.setCurrentIndex(i)
        if init_cat:
            i = self.cmb_cat.findData(init_cat)
            if i >= 0:
                self.cmb_cat.setCurrentIndex(i)
        if prefill_xy:
            self.sp_x.setValue(int(prefill_xy[0]))
            self.sp_y.setValue(int(prefill_xy[1]))

        self._refresh_table()

    def _request_pick(self):
        """Record the current map/category and close so the overlay can enter
        pick mode; the overlay reopens this editor with the picked coords."""
        self.pick_requested = True
        self.pick_map = self._cur_map()
        self.pick_cat = self._cur_cat()
        self.accept()

    def _cur_map(self) -> str:
        return self.cmb_map.currentData()

    def _cur_cat(self) -> str:
        return self.cmb_cat.currentData()

    def _refresh_table(self):
        pts = user_data.get_points(self.result_pois, self._cur_map(), self._cur_cat())
        self.table.setRowCount(len(pts))
        for r, pt in enumerate(pts):
            c = pt.get("c", [0, 0])
            x = c[0] if len(c) > 0 else 0
            y = c[1] if len(c) > 1 else 0
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(x)))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(str(y)))
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(str(pt.get("d", ""))))

    def _add_point(self):
        try:
            self.result_pois = user_data.add_point(
                self.result_pois, self._cur_map(), self._cur_cat(),
                self.sp_x.value(), self.sp_y.value(), self.ed_desc.text().strip(),
            )
        except ValueError:
            QtWidgets.QMessageBox.warning(
                self, tr("Edit Custom POIs"), tr("Invalid coordinates (need 0-4095)."))
            return
        self.ed_desc.clear()
        self._refresh_table()

    def _delete_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.result_pois = user_data.remove_point(
                self.result_pois, self._cur_map(), self._cur_cat(), r)
        self._refresh_table()

    def _export(self):
        """Show exported text (data.json-compatible) for copy/share."""
        text = transfer.export_user_pois(self.result_pois)
        dlg = _TextDialog(tr("Export"), text, read_only=True, icon="", p=self)
        dlg.exec()

    def _import(self):
        """Prompt for pasted text and merge the parsed points in."""
        dlg = _TextDialog(tr("Import"), "", read_only=False, icon="", p=self)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        text = dlg.text()
        if not text.strip():
            return
        try:
            self.result_pois = transfer.import_user_pois(text, base=self.result_pois)
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, tr("Import"), str(e))
            return
        self._refresh_table()


class _TextDialog(QtWidgets.QDialog):
    """Simple text box for export (read-only, with copy) and import (paste)."""

    def __init__(self, title: str, text: str = "", read_only: bool = False,
                 icon: str = "", p=None):
        super().__init__(p)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.resize(420, 360)
        self.setStyleSheet(
            "QWidget{background:#1e1f22;color:#e6e6e6;font-size:12px;}"
            "QPlainTextEdit{background:#2b2d30;color:#e6e6e6;border:1px solid #3a3c40;}"
            "QPushButton{background:#2b2d30;border:1px solid #3a3c40;padding:4px 10px;}"
            "QPushButton:hover{background:#34363a;}"
        )
        v = QtWidgets.QVBoxLayout(self)
        self.edit = QtWidgets.QPlainTextEdit()
        self.edit.setPlainText(text)
        self.edit.setReadOnly(read_only)
        v.addWidget(self.edit, 1)

        row = QtWidgets.QHBoxLayout()
        if read_only:
            btn_copy = QtWidgets.QPushButton(tr("Copy to Clipboard"))
            btn_copy.clicked.connect(self._copy)
            row.addWidget(btn_copy)
            row.addStretch(1)
            btn_ok = QtWidgets.QPushButton(tr("Close"))
            btn_ok.clicked.connect(self.accept)
            row.addWidget(btn_ok)
        else:
            self.edit.setPlaceholderText(tr("Paste exported data here"))
            row.addStretch(1)
            btn_cancel = QtWidgets.QPushButton(tr("Cancel"))
            btn_cancel.clicked.connect(self.reject)
            row.addWidget(btn_cancel)
            btn_ok = QtWidgets.QPushButton(tr("Import"))
            btn_ok.clicked.connect(self.accept)
            row.addWidget(btn_ok)
        v.addLayout(row)

    def text(self) -> str:
        return self.edit.toPlainText()

    def _copy(self):
        QtWidgets.QApplication.clipboard().setText(self.edit.toPlainText())


