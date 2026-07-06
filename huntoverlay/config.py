"""Config schema, defaults, merge, and load/migrate logic.

Pure logic plus JSON persistence via paths.*; no Qt. The default keybinds
and rect ratios come from constants/geometry so this stays the single
source of truth for config shape.
"""

import os

from . import constants
from .geometry import default_rect_ratio_by_aspect
from .paths import load_json, save_json


def default_keybinds():
    """
    Keybind schema is stored under settings.keybinds
    Each action is a dict:
      vk: int virtual key code
      ctrl alt shift: optional booleans for modifier gated binds
    Only hide_hovered uses modifiers by default.
    """
    return {
        "toggle_master": {"vk": constants.VK_BT},
        "toggle_overlay": {"vk": constants.VK_TAB},
        "hide_overlay": {"vk": constants.VK_H},
        "map_1": {"vk": constants.VK1},
        "map_2": {"vk": constants.VK2},
        "map_3": {"vk": constants.VK3},
        "map_4": {"vk": constants.VK4},
        "hide_hovered": {"vk": constants.VK_DELETE, "ctrl": True, "alt": True, "shift": True},
    }


def vk_to_label(vk: int) -> str:
    if vk == constants.VK_TAB:
        return "Tab"
    if vk == constants.VK_BT:
        return "`"
    if vk == constants.VK_DELETE:
        return "Delete"
    if vk == constants.VK_SHIFT:
        return "Shift"
    if vk == constants.VK_CONTROL:
        return "Ctrl"
    if vk == constants.VK_MENU:
        return "Alt"
    if 0x30 <= vk <= 0x39:
        return chr(vk)
    if 0x41 <= vk <= 0x5A:
        return chr(vk)
    if vk == constants.VK_ESC:
        return "Esc"
    return f"VK_{vk}"


def build_default_config():
    profiles = {}
    for m in constants.MAPS:
        profiles[m] = {"rect_ratio_by_aspect": default_rect_ratio_by_aspect()}
    return {
        "version": constants.CONFIG_VERSION,
        "profiles": profiles,
        "settings": {
            "enable_num_switch": True,
            "selected_map": constants.MAPS[0],
            "visible_overlay": False,
            "master_on": True,
            "global_scale": 1.00,
            "show_tray_icon": False,
            "minimize_to_tray": False,
            "start_hidden_to_tray": False,
            "hold_tab_to_show": False,
            "block_shift_tab": True,
            "show_user_pois": True,
            "keybinds": default_keybinds(),
            "types": {},
            "hidden": {"possible_xp": list(constants.DEFAULT_HIDDEN_POSSIBLE_XP)},
        },
    }


def deep_merge(default: dict, existing: dict) -> dict:
    """
    Merge existing user config into default.
    - New keys from default are added.
    - Existing user values are preserved.
    - Dicts are merged recursively.
    """
    result = {}
    for k, v in default.items():
        if k not in existing:
            result[k] = v
        elif isinstance(v, dict) and isinstance(existing[k], dict):
            result[k] = deep_merge(v, existing[k])
        else:
            result[k] = existing[k]
    return result


def load_or_replace_config(config_path: str):
    """
    If config.json is missing or unreadable, write and return fresh defaults.
    If the version is outdated, migrate by merging user values into the new
    defaults. User settings are preserved across version updates.
    """
    if not os.path.isfile(config_path):
        d = build_default_config()
        save_json(config_path, d)
        return d

    try:
        d = load_json(config_path)
    except (OSError, ValueError):
        d = {}

    if not isinstance(d, dict):
        d = build_default_config()
        save_json(config_path, d)
        return d

    if d.get("version") != constants.CONFIG_VERSION:
        d = deep_merge(build_default_config(), d)
        # Always apply the latest default rect ratios on version change so that
        # map coordinate updates from Hunt patches are picked up automatically.
        fresh_rects = default_rect_ratio_by_aspect()
        for m in constants.MAPS:
            if isinstance(d.get("profiles", {}).get(m), dict):
                d["profiles"][m]["rect_ratio_by_aspect"] = fresh_rects
        d["version"] = constants.CONFIG_VERSION
        save_json(config_path, d)

    return d
