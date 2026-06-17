"""Unit tests for huntoverlay.user_data — user POI storage and merge."""

import os

import pytest

from huntoverlay.user_data import (
    empty_user_pois,
    coord_valid,
    get_points,
    add_point,
    remove_point,
    merge_into_points,
    load_user_pois,
    save_user_pois,
    USER_POIS_VERSION,
)


@pytest.mark.unit
def test_empty_structure():
    e = empty_user_pois()
    assert e == {"version": USER_POIS_VERSION, "maps": {}}


@pytest.mark.unit
@pytest.mark.parametrize(
    "x,y,ok",
    [
        (0, 0, True),
        (4095, 4095, True),
        (2000, 3000, True),
        (-1, 0, False),
        (0, 4096, False),
        (4096, 0, False),
        ("abc", 0, False),
        (None, None, False),
    ],
)
def test_coord_valid(x, y, ok):
    assert coord_valid(x, y) is ok


@pytest.mark.unit
def test_add_point_is_immutable():
    base = empty_user_pois()
    new = add_point(base, "DeSalle", "armories", 100, 200, "note")
    # original untouched
    assert base == {"version": USER_POIS_VERSION, "maps": {}}
    # new has the point
    pts = get_points(new, "DeSalle", "armories")
    assert len(pts) == 1
    assert pts[0]["c"] == [100, 200]
    assert pts[0]["_user"] is True
    assert pts[0]["d"] == "note"


@pytest.mark.unit
def test_add_point_rounds_floats():
    new = add_point(empty_user_pois(), "DeSalle", "spawns", 100.6, 200.4)
    assert get_points(new, "DeSalle", "spawns")[0]["c"] == [101, 200]


@pytest.mark.unit
def test_add_point_without_desc_omits_d():
    new = add_point(empty_user_pois(), "DeSalle", "spawns", 1, 2)
    assert "d" not in get_points(new, "DeSalle", "spawns")[0]


@pytest.mark.unit
def test_add_point_with_images():
    new = add_point(empty_user_pois(), "DeSalle", "armories", 1, 2, "n",
                    images=["http://a/1.png", "http://a/2.png"])
    pt = get_points(new, "DeSalle", "armories")[0]
    assert pt["u"] == ["http://a/1.png", "http://a/2.png"]


@pytest.mark.unit
def test_add_point_blank_images_omits_u():
    new = add_point(empty_user_pois(), "DeSalle", "spawns", 1, 2, images=["", "  "])
    assert "u" not in get_points(new, "DeSalle", "spawns")[0]
    new2 = add_point(empty_user_pois(), "DeSalle", "spawns", 1, 2)
    assert "u" not in get_points(new2, "DeSalle", "spawns")[0]


@pytest.mark.unit
def test_add_point_rejects_out_of_range():
    with pytest.raises(ValueError):
        add_point(empty_user_pois(), "DeSalle", "spawns", 5000, 0)


@pytest.mark.unit
def test_add_multiple_points_accumulate():
    d = empty_user_pois()
    d = add_point(d, "DeSalle", "armories", 1, 1)
    d = add_point(d, "DeSalle", "armories", 2, 2)
    assert len(get_points(d, "DeSalle", "armories")) == 2


@pytest.mark.unit
def test_remove_point_is_immutable():
    d = add_point(empty_user_pois(), "DeSalle", "armories", 1, 1)
    d = add_point(d, "DeSalle", "armories", 2, 2)
    new = remove_point(d, "DeSalle", "armories", 0)
    # original keeps both
    assert len(get_points(d, "DeSalle", "armories")) == 2
    # new dropped the first
    remaining = get_points(new, "DeSalle", "armories")
    assert len(remaining) == 1 and remaining[0]["c"] == [2, 2]


@pytest.mark.unit
def test_remove_point_out_of_range_noop():
    d = add_point(empty_user_pois(), "DeSalle", "armories", 1, 1)
    new = remove_point(d, "DeSalle", "armories", 99)
    assert len(get_points(new, "DeSalle", "armories")) == 1


@pytest.mark.unit
def test_get_points_absent_returns_empty():
    assert get_points(empty_user_pois(), "Nope", "spawns") == []
    assert get_points(None, "x", "y") == []


@pytest.mark.unit
def test_merge_order_user_on_top():
    remote = [{"c": [1, 1]}, {"c": [2, 2]}]
    user = [{"c": [3, 3], "_user": True}]
    merged = merge_into_points(remote, user)
    assert merged == [{"c": [1, 1]}, {"c": [2, 2]}, {"c": [3, 3], "_user": True}]
    # inputs not mutated
    assert len(remote) == 2 and len(user) == 1


@pytest.mark.unit
def test_merge_defensive():
    assert merge_into_points(None, None) == []
    assert merge_into_points([{"c": [1, 1]}], None) == [{"c": [1, 1]}]


@pytest.mark.unit
def test_load_missing_returns_empty(tmp_path):
    assert load_user_pois(os.path.join(tmp_path, "nope.json")) == empty_user_pois()


@pytest.mark.unit
def test_load_corrupt_returns_empty(tmp_path):
    p = os.path.join(tmp_path, "u.json")
    with open(p, "w", encoding="utf-8") as f:
        f.write("{ not valid json")
    assert load_user_pois(p) == empty_user_pois()


@pytest.mark.unit
def test_load_wrong_shape_returns_empty(tmp_path):
    p = os.path.join(tmp_path, "u.json")
    save_user_pois(p, {"foo": "bar"})  # no "maps" key
    assert load_user_pois(p) == empty_user_pois()


@pytest.mark.unit
def test_save_then_load_roundtrip(tmp_path):
    p = os.path.join(tmp_path, "u.json")
    d = add_point(empty_user_pois(), "DeSalle", "armories", 123, 456, "x")
    save_user_pois(p, d)
    loaded = load_user_pois(p)
    assert get_points(loaded, "DeSalle", "armories")[0]["c"] == [123, 456]
