"""Pure parsing helpers for the POI data and style JSON.

No Qt, no I/O, no network — just interpreting already-loaded structures.
Two on-disk formats are supported (see detect_data_format).
"""

from .constants import MAPS


def detect_data_format(game_data) -> str:
    """
    Supports two formats
    indexed_r: list of dicts with "i" map index and "r" categories
    named: list of dicts with "n" map name and direct category arrays
    """
    if isinstance(game_data, list) and game_data:
        a = game_data[0]
        if isinstance(a, dict) and "i" in a and ("r" in a or "a" in a):
            return "indexed_r"
        if isinstance(a, dict) and "n" in a:
            return "named"
    return "unknown"


def get_map_block(game_data, fmt: str, map_name: str):
    if fmt == "named":
        for m in game_data:
            if isinstance(m, dict) and m.get("n") == map_name:
                return m
        return None

    if fmt == "indexed_r":
        try:
            idx = MAPS.index(map_name)
        except ValueError:
            return None

        for m in game_data:
            if isinstance(m, dict) and m.get("i") == idx:
                return m
        return None

    return None


def get_category_list(map_block, fmt: str, category: str):
    if not isinstance(map_block, dict):
        return []
    if fmt == "named":
        v = map_block.get(category, [])
        return v if isinstance(v, list) else []
    if fmt == "indexed_r":
        r = map_block.get("r", {})
        if isinstance(r, dict):
            v = r.get(category, [])
            return v if isinstance(v, list) else []
        return []
    return []


def find_style_by_category(style_json, category: str):
    if not isinstance(style_json, dict):
        return None
    for _, spec in style_json.items():
        if isinstance(spec, dict) and spec.get("categories") == category:
            return spec
    return None
