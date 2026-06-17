"""Unit tests for huntoverlay.boss_data — static boss reference data."""

import pytest

from huntoverlay import boss_data
from huntoverlay.i18n import tr


@pytest.mark.unit
def test_boss_keys_are_the_four_traditional():
    assert boss_data.boss_keys() == ["butcher", "spider", "assassin", "scrapbeak"]


@pytest.mark.unit
def test_get_boss_unknown_returns_none():
    assert boss_data.get_boss("hellborn") is None


@pytest.mark.unit
@pytest.mark.parametrize("key", ["butcher", "spider", "assassin", "scrapbeak"])
def test_every_boss_has_required_fields(key):
    b = boss_data.get_boss(key)
    assert b is not None
    assert b["name"]
    assert b["fire"] in (boss_data.WEAK, boss_data.IMMUNE, boss_data.NORMAL)
    assert b["poison"] in (boss_data.WEAK, boss_data.IMMUNE, boss_data.NORMAL)
    assert isinstance(b["tips"], list) and b["tips"]


@pytest.mark.unit
def test_known_resistances():
    # The community-agreed facts the feature is built on.
    assert boss_data.get_boss("butcher")["fire"] == boss_data.IMMUNE
    assert boss_data.get_boss("spider")["fire"] == boss_data.WEAK
    assert boss_data.get_boss("spider")["poison"] == boss_data.IMMUNE
    assert boss_data.get_boss("assassin")["fire"] == boss_data.WEAK


@pytest.mark.unit
def test_no_banish_time_or_hp_fields():
    # Intentionally omitted — uncertain across patches.
    for key in boss_data.boss_keys():
        b = boss_data.get_boss(key)
        assert "banish" not in b
        assert "hp" not in b


@pytest.mark.unit
def test_all_boss_names_and_tips_have_zh_translations():
    # Every English string in boss_data must have a zh translation, or the
    # Chinese UI would show English. tr() returns the key itself if missing,
    # so a missing translation == tr(x) == x.
    import huntoverlay.i18n as i18n
    i18n.set_language("zh")
    try:
        for key in boss_data.boss_keys():
            b = boss_data.get_boss(key)
            assert tr(b["name"]) != b["name"], f"missing zh for boss name {b['name']}"
            for tip in b["tips"]:
                assert tr(tip) != tip, f"missing zh for tip: {tip}"
    finally:
        i18n.set_language(i18n.DEFAULT_LANG)
