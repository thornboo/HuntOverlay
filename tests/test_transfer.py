"""Unit tests for huntoverlay.transfer — POI import/export."""

import json

import pytest

from huntoverlay import transfer, user_data


def _sample():
    d = user_data.empty_user_pois()
    d = user_data.add_point(d, "DeSalle", "armories", 1234, 3456, "note")
    d = user_data.add_point(d, "DeSalle", "spawns", 100, 200)
    d = user_data.add_point(d, "Lawson Delta", "towers", 500, 600)
    return d


@pytest.mark.unit
def test_export_is_valid_json_and_data_shape():
    out = transfer.export_user_pois(_sample())
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    names = {b["n"] for b in parsed}
    assert names == {"DeSalle", "Lawson Delta"}


@pytest.mark.unit
def test_export_strips_user_marker():
    out = transfer.export_user_pois(_sample())
    assert "_user" not in out
    parsed = json.loads(out)
    de = next(b for b in parsed if b["n"] == "DeSalle")
    assert de["armories"][0] == {"c": [1234, 3456], "d": "note"}
    assert de["spawns"][0] == {"c": [100, 200]}  # no empty "d"


@pytest.mark.unit
def test_export_empty():
    out = transfer.export_user_pois(user_data.empty_user_pois())
    assert json.loads(out) == []


@pytest.mark.unit
def test_export_import_round_trip():
    original = _sample()
    text = transfer.export_user_pois(original)
    imported = transfer.import_user_pois(text)
    # Same points come back (compare per map+category counts and coords).
    for mp, cat in [("DeSalle", "armories"), ("DeSalle", "spawns"), ("Lawson Delta", "towers")]:
        a = user_data.get_points(original, mp, cat)
        b = user_data.get_points(imported, mp, cat)
        assert [p["c"] for p in a] == [p["c"] for p in b]


@pytest.mark.unit
def test_export_import_preserves_images():
    d = user_data.add_point(user_data.empty_user_pois(), "DeSalle", "armories",
                            10, 20, "n", images=["http://a/1.png"])
    text = transfer.export_user_pois(d)
    assert "http://a/1.png" in text
    back = transfer.import_user_pois(text)
    assert user_data.get_points(back, "DeSalle", "armories")[0]["u"] == ["http://a/1.png"]


@pytest.mark.unit
def test_import_invalid_json_raises():
    with pytest.raises(ValueError):
        transfer.import_user_pois("{ not json")


@pytest.mark.unit
def test_import_non_list_raises():
    with pytest.raises(ValueError):
        transfer.import_user_pois('{"n": "DeSalle"}')


@pytest.mark.unit
def test_import_skips_out_of_range_points():
    text = json.dumps([{"n": "DeSalle", "armories": [
        {"c": [9999, 0]},      # out of range -> skipped
        {"c": [10, 20]},       # valid
    ]}])
    out = transfer.import_user_pois(text)
    pts = user_data.get_points(out, "DeSalle", "armories")
    assert len(pts) == 1 and pts[0]["c"] == [10, 20]


@pytest.mark.unit
def test_import_supports_indexed_blocks():
    # data.json indexed form: block keyed by "i" instead of "n".
    text = json.dumps([{"i": 2, "armories": [{"c": [10, 20]}]}])  # i=2 -> DeSalle
    out = transfer.import_user_pois(text)
    assert len(user_data.get_points(out, "DeSalle", "armories")) == 1


@pytest.mark.unit
def test_import_merges_onto_base():
    base = user_data.add_point(user_data.empty_user_pois(), "DeSalle", "spawns", 1, 2)
    text = json.dumps([{"n": "DeSalle", "armories": [{"c": [10, 20]}]}])
    out = transfer.import_user_pois(text, base=base)
    assert len(user_data.get_points(out, "DeSalle", "spawns")) == 1
    assert len(user_data.get_points(out, "DeSalle", "armories")) == 1


@pytest.mark.unit
def test_import_ignores_unknown_map():
    text = json.dumps([{"n": "Nonexistent Map", "armories": [{"c": [10, 20]}]}])
    out = transfer.import_user_pois(text)
    assert out.get("maps", {}) == {}
