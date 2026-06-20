"""Unit tests for overlay tool repaint regions."""

import importlib
import sys

import pytest
from PySide6 import QtCore


def _load_overlay(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    sys.modules.pop("huntoverlay.overlay", None)
    sys.modules.pop("huntoverlay.runtime", None)
    return importlib.import_module("huntoverlay.overlay")


class _RegionState:
    def __init__(self, overlay):
        self._overlay = overlay
        self.rect = QtCore.QRect(100, 100, 400, 300)

    def width(self):
        return 800

    def height(self):
        return 600

    def _tool_bounds(self):
        return self._overlay.Overlay._tool_bounds(self)

    def _bounded_region(self, region):
        return self._overlay.Overlay._bounded_region(self, region)

    def _point_dirty_region(self, pos, label_width=220, label_height=76):
        return self._overlay.Overlay._point_dirty_region(self, pos, label_width, label_height)


@pytest.mark.unit
def test_pick_dirty_region_tracks_crosshair_stripes(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    state = _RegionState(overlay)

    region = overlay.Overlay._pick_dirty_region(state, QtCore.QPointF(200, 150))

    assert region.contains(QtCore.QPoint(200, 250))  # vertical crosshair
    assert region.contains(QtCore.QPoint(300, 150))  # horizontal crosshair
    assert not region.contains(QtCore.QPoint(300, 250))  # outside both stripes


@pytest.mark.unit
def test_line_dirty_region_tracks_line_not_bounding_rect(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    state = _RegionState(overlay)

    region = overlay.Overlay._line_dirty_region(state, 100, 100, 500, 400)

    assert region.contains(QtCore.QPoint(300, 250))  # near the line midpoint
    assert not region.contains(QtCore.QPoint(300, 390))  # inside bbox, far from line


@pytest.mark.unit
def test_same_pixel_suppresses_duplicate_mouse_moves(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)

    assert overlay.Overlay._same_pixel(None, None, QtCore.QPointF(1.2, 1.9)) is False
    assert overlay.Overlay._same_pixel(
        None,
        QtCore.QPointF(12.2, 9.9),
        QtCore.QPointF(12.8, 9.1),
    ) is True
    assert overlay.Overlay._same_pixel(
        None,
        QtCore.QPointF(12.2, 9.9),
        QtCore.QPointF(13.0, 9.1),
    ) is False
