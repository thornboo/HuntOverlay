"""Unit tests for huntoverlay.config — defaults, merge, load/migrate."""

import json
import os

import pytest

from huntoverlay.config import (
    build_default_config,
    deep_merge,
    default_keybinds,
    load_or_replace_config,
    vk_to_label,
)
from huntoverlay.constants import MAPS, CONFIG_VERSION


@pytest.mark.unit
def test_build_default_config_shape():
    cfg = build_default_config()
    assert cfg["version"] == CONFIG_VERSION
    assert set(cfg["profiles"]) == set(MAPS)
    s = cfg["settings"]
    for key in ("selected_map", "global_scale", "show_user_pois", "keybinds", "types", "hidden"):
        assert key in s
    assert s["selected_map"] == MAPS[0]
    assert s["show_user_pois"] is True


@pytest.mark.unit
def test_default_keybinds_has_all_actions():
    kb = default_keybinds()
    for action in ("toggle_master", "toggle_overlay", "hide_overlay",
                   "map_1", "map_2", "map_3", "map_4", "hide_hovered"):
        assert "vk" in kb[action]
    # hide_hovered is the only modifier-gated bind by default
    assert kb["hide_hovered"].get("ctrl") and kb["hide_hovered"].get("shift")


@pytest.mark.unit
def test_deep_merge_adds_missing_keys():
    assert deep_merge({"a": 1, "b": 2}, {"a": 9}) == {"a": 9, "b": 2}


@pytest.mark.unit
def test_deep_merge_preserves_user_values():
    assert deep_merge({"a": 1}, {"a": 42}) == {"a": 42}


@pytest.mark.unit
def test_deep_merge_recursive():
    default = {"s": {"x": 1, "y": 2, "z": 3}}
    existing = {"s": {"y": 99}}
    assert deep_merge(default, existing) == {"s": {"x": 1, "y": 99, "z": 3}}


@pytest.mark.unit
def test_deep_merge_type_mismatch_takes_existing():
    # If user value is not a dict but default is, user value wins.
    assert deep_merge({"a": {"x": 1}}, {"a": "scalar"}) == {"a": "scalar"}


@pytest.mark.unit
def test_load_creates_default_when_missing(tmp_path):
    cfg_path = os.path.join(tmp_path, "config.json")
    cfg = load_or_replace_config(cfg_path)
    assert os.path.isfile(cfg_path)
    assert cfg["version"] == CONFIG_VERSION


@pytest.mark.unit
def test_load_replaces_non_dict(tmp_path):
    cfg_path = os.path.join(tmp_path, "config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(["not", "a", "dict"], f)
    cfg = load_or_replace_config(cfg_path)
    assert isinstance(cfg, dict) and cfg["version"] == CONFIG_VERSION


@pytest.mark.unit
def test_load_migrates_old_version_preserving_settings(tmp_path):
    cfg_path = os.path.join(tmp_path, "config.json")
    old = build_default_config()
    old["version"] = "0.0.1"
    old["settings"]["global_scale"] = 1.75   # user customization to preserve
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(old, f)

    cfg = load_or_replace_config(cfg_path)
    assert cfg["version"] == CONFIG_VERSION
    assert cfg["settings"]["global_scale"] == 1.75  # preserved across migration


@pytest.mark.unit
def test_load_keeps_current_version_untouched(tmp_path):
    cfg_path = os.path.join(tmp_path, "config.json")
    cur = build_default_config()
    cur["settings"]["selected_map"] = MAPS[2]
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cur, f)
    cfg = load_or_replace_config(cfg_path)
    assert cfg["settings"]["selected_map"] == MAPS[2]


@pytest.mark.unit
@pytest.mark.parametrize(
    "vk,expected",
    [
        (0x09, "Tab"),
        (0xC0, "`"),
        (0x2E, "Delete"),
        (0x10, "Shift"),
        (0x11, "Ctrl"),
        (0x12, "Alt"),
        (0x1B, "Esc"),
        (0x31, "1"),    # digit range
        (0x39, "9"),
        (0x41, "A"),    # letter range
        (0x5A, "Z"),
        (0x70, "VK_112"),  # F1, unmapped -> raw label
    ],
)
def test_vk_to_label(vk, expected):
    assert vk_to_label(vk) == expected
