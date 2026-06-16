"""Unit tests for huntoverlay.i18n — multi-language label lookups."""

import pytest

from huntoverlay import i18n


@pytest.fixture(autouse=True)
def _reset_language():
    """Each test starts from the default language and restores it after."""
    i18n.set_language(i18n.DEFAULT_LANG)
    yield
    i18n.set_language(i18n.DEFAULT_LANG)


@pytest.mark.unit
def test_default_language_is_zh():
    assert i18n.DEFAULT_LANG == "zh"
    assert i18n.get_language() == "zh"


@pytest.mark.unit
def test_available_languages():
    codes = [c for c, _ in i18n.available_languages()]
    assert "zh" in codes and "en" in codes


@pytest.mark.unit
def test_set_language_switches():
    i18n.set_language("en")
    assert i18n.get_language() == "en"


@pytest.mark.unit
def test_set_language_ignores_unknown():
    i18n.set_language("zh")
    i18n.set_language("xx")  # unknown -> keep current
    assert i18n.get_language() == "zh"


@pytest.mark.unit
def test_map_display_zh_default():
    assert i18n.map_display("Stillwater Bayou") == "静水河口"
    assert i18n.map_display("Lawson Delta") == "劳森三角洲"
    assert i18n.map_display("DeSalle") == "德萨莱"
    assert i18n.map_display("Mammon's Gulch") == "玛门峡谷"


@pytest.mark.unit
def test_map_display_en():
    i18n.set_language("en")
    assert i18n.map_display("DeSalle") == "DeSalle"
    assert i18n.map_display("Stillwater Bayou") == "Stillwater Bayou"


@pytest.mark.unit
def test_map_display_unknown_falls_back_to_name():
    assert i18n.map_display("Nowhere") == "Nowhere"
    i18n.set_language("en")
    assert i18n.map_display("Nowhere") == "Nowhere"


@pytest.mark.unit
def test_category_label_zh_and_en():
    assert i18n.category_label("spawns", "fallback") == "出生点"
    i18n.set_language("en")
    assert i18n.category_label("spawns", "fallback") == "Spawns"


@pytest.mark.unit
def test_category_label_unknown_uses_fallback():
    assert i18n.category_label("nope", "MyFallback") == "MyFallback"


@pytest.mark.unit
def test_action_label_zh_and_en():
    assert i18n.action_label("toggle_master") == "总开关"
    i18n.set_language("en")
    assert i18n.action_label("toggle_master") == "Toggle master"


@pytest.mark.unit
def test_action_labels_returns_full_map():
    labels = i18n.action_labels()
    for key in ("toggle_master", "toggle_overlay", "hide_overlay",
                "map_1", "map_2", "map_3", "map_4", "hide_hovered"):
        assert key in labels
    assert labels["toggle_master"] == "总开关"


@pytest.mark.unit
def test_every_map_has_both_languages():
    for name in ("Stillwater Bayou", "Lawson Delta", "DeSalle", "Mammon's Gulch"):
        zh = i18n.map_display(name)
        i18n.set_language("en")
        en = i18n.map_display(name)
        i18n.set_language("zh")
        assert zh and en


@pytest.mark.unit
def test_english_fallback_when_current_lang_used():
    i18n.set_language("en")
    assert i18n.category_label("brutes", "x") == "Brutes"
