"""Unit tests for overlay tool repaint regions."""

import importlib
import sys
from types import SimpleNamespace

import pytest
from PySide6 import QtCore, QtGui


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


@pytest.mark.unit
def test_poll_tool_cursor_updates_pick_from_timer(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    state = SimpleNamespace(
        visible=True,
        _pick_mode=True,
        _ruler_mode=False,
        cursor=QtCore.QPointF(123, 234),
        called=None,
    )
    state._tool_cursor_pos = lambda: state.cursor
    state._set_pick_pos = lambda pos: setattr(state, "called", ("pick", pos))
    state._set_ruler_pos = lambda pos: setattr(state, "called", ("ruler", pos))

    overlay.Overlay._poll_tool_cursor(state)

    mode, pos = state.called
    assert mode == "pick"
    assert pos == QtCore.QPointF(123, 234)


@pytest.mark.unit
def test_poll_tool_cursor_updates_ruler_from_timer(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    state = SimpleNamespace(
        visible=True,
        _pick_mode=False,
        _ruler_mode=True,
        cursor=QtCore.QPointF(321, 432),
        called=None,
    )
    state._tool_cursor_pos = lambda: state.cursor
    state._set_pick_pos = lambda pos: setattr(state, "called", ("pick", pos))
    state._set_ruler_pos = lambda pos: setattr(state, "called", ("ruler", pos))

    overlay.Overlay._poll_tool_cursor(state)

    mode, pos = state.called
    assert mode == "ruler"
    assert pos == QtCore.QPointF(321, 432)


@pytest.mark.unit
def test_update_region_repaints_immediately(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    calls = []

    class _State:
        def repaint(self, *args):
            calls.append(args)

    region = QtGui.QRegion(QtCore.QRect(1, 2, 3, 4))
    overlay.Overlay._update_region(_State(), region)

    assert len(calls) == 1
    assert calls[0][0] is region


@pytest.mark.unit
def test_start_poi_pick_mode_uses_real_category(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    calls = []
    state = SimpleNamespace(
        type_order=["possible_xp", "armories", "towers"],
        prof="DeSalle",
        _enter_pick_mode=lambda map_name, category: calls.append((map_name, category)),
    )

    overlay.Overlay._start_poi_pick_mode(state, "possible_xp")

    assert calls == [("DeSalle", "armories")]


@pytest.mark.unit
def test_set_show_user_pois_rebuilds_cache_and_prefetches(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    calls = []
    state = SimpleNamespace(
        show_user_pois=False,
        _rebuild_all_caches=lambda: calls.append("rebuild"),
        _start_image_prefetch=lambda: calls.append("prefetch"),
        _save=lambda: calls.append("save"),
        update=lambda: calls.append("update"),
    )

    overlay.Overlay._set_show_user_pois(state, True)

    assert state.show_user_pois is True
    assert calls == ["rebuild", "prefetch", "save", "update"]


@pytest.mark.unit
def test_build_points_respects_show_user_pois(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    monkeypatch.setattr(
        overlay,
        "get_map_block",
        lambda game_data, fmt, map_name: {"n": map_name},
    )

    def category_points(_block, _fmt, category):
        if category == "armories":
            return [{"c": [10, 20]}]
        return []

    monkeypatch.setattr(overlay, "get_category_list", category_points)
    user_pois = overlay.user_data.add_point(
        overlay.user_data.empty_user_pois(),
        "DeSalle",
        "armories",
        30,
        40,
    )
    user_pois = overlay.user_data.add_point(
        user_pois,
        "DeSalle",
        "armories",
        50,
        60,
    )
    user_pois = overlay.user_data.set_point_visible(
        user_pois,
        "DeSalle",
        "armories",
        1,
        False,
    )
    state = SimpleNamespace(
        game_data=[],
        fmt="legacy",
        type_order=["possible_xp", "armories", "towers", "big_towers"],
        user_pois=user_pois,
        show_user_pois=False,
    )

    hidden = overlay.Overlay._build_points_for_map(state, "DeSalle")
    state.show_user_pois = True
    visible = overlay.Overlay._build_points_for_map(state, "DeSalle")

    assert len(hidden["armories"]) == 1
    assert len(visible["armories"]) == 2
    assert visible["armories"][1]["raw"]["_user"] is True
    assert visible["armories"][1]["x"] == 30.0


@pytest.mark.unit
def test_clear_rulers_removes_all_maps(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    calls = []
    state = SimpleNamespace(
        prof="DeSalle",
        _rulers=[
            {"map": "DeSalle", "a": (1, 2), "b": (3, 4)},
            {"map": "Lawson Delta", "a": (5, 6), "b": (7, 8)},
        ],
        _ruler_hover_delete=(0, "a"),
        update=lambda: calls.append("update"),
    )

    overlay.Overlay._clear_rulers(state)

    assert state._rulers == []
    assert state._ruler_hover_delete is None
    assert calls == ["update"]
