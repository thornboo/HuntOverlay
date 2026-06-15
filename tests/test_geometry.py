"""Unit tests for huntoverlay.geometry — pure math, no Qt."""

import pytest

from huntoverlay.geometry import (
    detect_aspect_label,
    default_rect_ratio_16_9,
    default_rect_ratio_by_aspect,
    rotate90cw_norm,
    overlay_radius_from_spec,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "w,h,expected",
    [
        (1920, 1080, "16:9"),
        (3840, 2160, "16:9"),
        (2560, 1440, "16:9"),
        (3440, 1440, "21:9"),
        (3840, 1600, "21:9"),
        (5120, 1440, "32:9"),
        (3840, 1080, "32:9"),
        (100, 0, "16:9"),     # h<=0 guard
        (100, -5, "16:9"),    # negative height guard
    ],
)
def test_detect_aspect_label(w, h, expected):
    assert detect_aspect_label(w, h) == expected


@pytest.mark.unit
def test_aspect_boundaries():
    # 2.20 is the 21:9 threshold (inclusive), 3.20 the 32:9 threshold.
    assert detect_aspect_label(220, 100) == "21:9"
    assert detect_aspect_label(219, 100) == "16:9"
    assert detect_aspect_label(320, 100) == "32:9"
    assert detect_aspect_label(319, 100) == "21:9"


@pytest.mark.unit
def test_rect_ratio_shapes():
    by = default_rect_ratio_by_aspect()
    assert set(by) == {"16:9", "21:9", "32:9"}
    for r in by.values():
        assert set(r) == {"rx", "ry", "rw", "rh"}
        assert all(0.0 <= v <= 1.0 for v in r.values())


@pytest.mark.unit
def test_rect_ratio_is_fresh_copy():
    # build_default_config relies on each call returning independent dicts.
    a = default_rect_ratio_16_9()
    b = default_rect_ratio_16_9()
    a["rx"] = 999
    assert b["rx"] != 999


@pytest.mark.unit
@pytest.mark.parametrize(
    "x,y,expected",
    [
        (0, 0, (0.0, 1.0)),
        (4095, 4095, (1.0, 0.0)),
        (4095, 0, (0.0, 0.0)),
        (0, 4095, (1.0, 1.0)),
    ],
)
def test_rotate90cw_norm_corners(x, y, expected):
    u, v = rotate90cw_norm(x, y)
    assert (round(u, 6), round(v, 6)) == expected


@pytest.mark.unit
def test_rotate90cw_norm_clamps_out_of_range():
    u, v = rotate90cw_norm(-1000, -1000)
    assert 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0
    u, v = rotate90cw_norm(99999, 99999)
    assert 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0


@pytest.mark.unit
@pytest.mark.parametrize(
    "spec,expected",
    [
        (12, 3),          # 12*0.25=3
        (40, 10),         # 40*0.25=10 (at ceiling)
        (100, 10),        # clamped to ceiling
        (0, 3),           # clamped to floor
        ("garbage", 3),   # non-numeric -> 12.0 default -> 3
        (None, 3),        # None -> default -> 3
    ],
)
def test_overlay_radius_from_spec(spec, expected):
    assert overlay_radius_from_spec(spec) == expected
