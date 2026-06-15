"""Unit tests for huntoverlay.mapdata — pure parsing, no Qt/IO."""

import pytest

from huntoverlay.mapdata import (
    detect_data_format,
    get_map_block,
    get_category_list,
    find_style_by_category,
)
from huntoverlay.constants import MAPS


@pytest.mark.unit
@pytest.mark.parametrize(
    "data,expected",
    [
        ([{"n": "Stillwater Bayou", "spawns": []}], "named"),
        ([{"i": 0, "r": {"spawns": []}}], "indexed_r"),
        ([{"i": 0, "a": []}], "indexed_r"),
        ([], "unknown"),
        ("not a list", "unknown"),
        ([{"x": 1}], "unknown"),
        (None, "unknown"),
    ],
)
def test_detect_data_format(data, expected):
    assert detect_data_format(data) == expected


@pytest.mark.unit
def test_get_map_block_named():
    data = [{"n": "DeSalle", "spawns": [[1, 2]]}, {"n": "Lawson Delta"}]
    block = get_map_block(data, "named", "DeSalle")
    assert block is not None and block["n"] == "DeSalle"
    assert get_map_block(data, "named", "Nonexistent") is None


@pytest.mark.unit
def test_get_map_block_indexed():
    # index follows MAPS order
    idx = MAPS.index("DeSalle")
    data = [{"i": idx, "r": {"spawns": []}}]
    block = get_map_block(data, "indexed_r", "DeSalle")
    assert block is not None and block["i"] == idx


@pytest.mark.unit
def test_get_map_block_unknown_map_and_format():
    assert get_map_block([{"i": 0}], "indexed_r", "NotAMap") is None
    assert get_map_block([{"n": "X"}], "bogus", "X") is None


@pytest.mark.unit
def test_get_category_list_named():
    block = {"n": "X", "spawns": [[1, 2], [3, 4]]}
    assert get_category_list(block, "named", "spawns") == [[1, 2], [3, 4]]
    assert get_category_list(block, "named", "missing") == []


@pytest.mark.unit
def test_get_category_list_indexed():
    block = {"i": 0, "r": {"armories": [[5, 6]]}}
    assert get_category_list(block, "indexed_r", "armories") == [[5, 6]]
    assert get_category_list(block, "indexed_r", "missing") == []


@pytest.mark.unit
def test_get_category_list_defensive():
    assert get_category_list(None, "named", "spawns") == []
    assert get_category_list({"n": "X", "spawns": "notalist"}, "named", "spawns") == []
    assert get_category_list({"i": 0, "r": "notadict"}, "indexed_r", "x") == []


@pytest.mark.unit
def test_find_style_by_category():
    style = {
        "k1": {"categories": "spawns", "radius": 12},
        "k2": {"categories": "armories", "radius": 8},
    }
    assert find_style_by_category(style, "armories") == {"categories": "armories", "radius": 8}
    assert find_style_by_category(style, "missing") is None
    assert find_style_by_category("notadict", "spawns") is None
