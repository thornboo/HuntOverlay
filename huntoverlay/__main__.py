"""Application entry point.

Builds the QApplication, applies the dark Fusion palette, and launches the
Overlay. Logic moved verbatim from the original single-file __main__ block;
only wrapped in main() so the root HuntOverlay.py shim and `python -m
huntoverlay` can both call it.
"""

import sys

from PySide6 import QtGui, QtWidgets

from .constants import APP_TITLE
from .runtime import ICON
from .overlay import Overlay


def main():
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setStyle("Fusion")

    # Consistent dark palette for the panel.
    pal = app.palette()
    for role, color in [
        (QtGui.QPalette.Window, QtGui.QColor(30, 31, 34)),
        (QtGui.QPalette.WindowText, QtGui.QColor(230, 230, 230)),
        (QtGui.QPalette.Base, QtGui.QColor(43, 45, 48)),
        (QtGui.QPalette.AlternateBase, QtGui.QColor(36, 38, 41)),
        (QtGui.QPalette.Text, QtGui.QColor(230, 230, 230)),
        (QtGui.QPalette.Button, QtGui.QColor(43, 45, 48)),
        (QtGui.QPalette.ButtonText, QtGui.QColor(230, 230, 230)),
        (QtGui.QPalette.Highlight, QtGui.QColor(90, 120, 200)),
        (QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255)),
    ]:
        pal.setColor(role, color)
    app.setPalette(pal)

    if ICON:
        app.setWindowIcon(QtGui.QIcon(ICON))

    try:
        w = Overlay()
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, f"{APP_TITLE}：错误", str(e))
        sys.exit(1)

    # Keep a reference so the overlay is not garbage-collected.
    _ = w
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
