"""Qt-side adapters that bridge pure data and QtGui types.

These need PySide6, so by Plan A they live outside the pure core. Colors
are stored in config as [r, g, b] lists; these helpers convert to/from
QColor and read the primary screen size.
"""

from PySide6 import QtGui


def q2rgb(c: QtGui.QColor):
    return [c.red(), c.green(), c.blue()]


def rgb2q(v, fallback=None) -> QtGui.QColor:
    fb = fallback if fallback is not None else QtGui.QColor(255, 180, 80)
    try:
        r, g, b = v
        return QtGui.QColor(int(r), int(g), int(b))
    except Exception:
        return QtGui.QColor(fb)


def qcolor_from_any(value, fallback: QtGui.QColor) -> QtGui.QColor:
    try:
        c = QtGui.QColor(str(value))
        return c if c.isValid() else QtGui.QColor(fallback)
    except Exception:
        return QtGui.QColor(fallback)


def screenWH():
    g = QtGui.QGuiApplication.primaryScreen().geometry()
    return g.width(), g.height()
