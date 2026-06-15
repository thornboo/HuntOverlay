"""Unit tests for huntoverlay.constants — label lookups."""

import pytest

from huntoverlay import constants
from huntoverlay.constants import category_label, map_display, MAPS, MAP_LABELS_ZH


@pytest.mark.unit
def test_map_display_known():
    assert map_display("Stillwater Bayou") == "静水河口"
    assert map_display("Lawson Delta") == "劳森三角洲"
    assert map_display("DeSalle") == "德萨莱"
    assert map_display("Mammon's Gulch") == "玛门峡谷"


@pytest.mark.unit
def test_map_display_falls_back_to_name():
    assert map_display("Unknown Map") == "Unknown Map"


@pytest.mark.unit
def test_every_map_has_a_label():
    for m in MAPS:
        assert m in MAP_LABELS_ZH


@pytest.mark.unit
def test_category_label_known_and_fallback():
    assert category_label("spawns", "fallback") == "出生点"
    assert category_label("nonexistent", "fallback") == "fallback"


@pytest.mark.unit
def test_data_urls_are_https():
    # Safety invariant: all remote sources must be https and on the known host.
    for url in (constants.DATA_URL, constants.STYLE_URL):
        assert url.startswith("https://hunt.kamille.ovh/")
