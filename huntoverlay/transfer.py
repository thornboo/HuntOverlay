"""Import / export of user POIs in a data.json-compatible format.

Lets users share points picked in-game (overlay v2) back to the community,
and pull community data in as editable user points. Pure logic + JSON
strings; no Qt, no network, no file I/O.

Export shape (mirrors data.json: a list of per-map blocks, points as
{"c": [x, y]} with optional "d"); the internal "_user" marker is dropped:

    [
      {"n": "DeSalle", "armories": [{"c": [1234, 3456], "d": "note"}]},
      ...
    ]

Import accepts that same shape (and tolerates the full data.json with extra
fields like "i"/"m"/"o"), turning every point into a user point.
"""

import json

from . import user_data
from .constants import MAPS

# Categories that are real POI lists in a map block (excludes metadata keys
# and the derived possible_xp union).
_EXPORT_CATEGORIES = [
    "spawns", "armories", "towers", "big_towers", "workbenches",
    "wild_targets", "brutes", "beetles", "easter_eggs",
    "melee_weapons", "cash_registers",
]

_META_KEYS = {"i", "n", "m", "o"}


def export_user_pois(data: dict) -> str:
    """Serialize user POIs to a data.json-compatible JSON string.

    Only maps/categories that actually have user points are emitted. Each
    point keeps its coordinate and description; the internal _user marker is
    stripped so the output matches the community format.
    """
    blocks = []
    maps = data.get("maps", {}) if isinstance(data, dict) else {}
    for map_name in MAPS:
        cats = maps.get(map_name, {})
        if not isinstance(cats, dict):
            continue
        block = {}
        for cat in _EXPORT_CATEGORIES:
            pts = cats.get(cat, [])
            if not isinstance(pts, list) or not pts:
                continue
            out_pts = []
            for pt in pts:
                if not isinstance(pt, dict) or "c" not in pt:
                    continue
                clean = {"c": list(pt["c"])}
                if pt.get("d"):
                    clean["d"] = pt["d"]
                out_pts.append(clean)
            if out_pts:
                block[cat] = out_pts
        if block:
            block["n"] = map_name
            blocks.append(block)
    return json.dumps(blocks, ensure_ascii=False, indent=2)


def import_user_pois(text: str, base: dict = None) -> dict:
    """Parse exported/data.json text and return a NEW user_pois dict with the
    parsed points added as user points (merged onto `base` if given).

    Raises ValueError if the text is not valid JSON or not the expected shape.
    Coordinates out of range are skipped (not fatal) so one bad point does not
    abort the whole import.
    """
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError) as e:
        raise ValueError(f"无法解析 JSON：{e}")

    if not isinstance(parsed, list):
        raise ValueError("格式错误：顶层应为地图块的数组")

    result = base if isinstance(base, dict) else user_data.empty_user_pois()
    result.setdefault("version", 1)
    result.setdefault("maps", {})

    for block in parsed:
        if not isinstance(block, dict):
            continue
        map_name = block.get("n")
        if map_name not in MAPS:
            # Support index-only blocks (data.json indexed form) via "i".
            idx = block.get("i")
            if isinstance(idx, int) and 0 <= idx < len(MAPS):
                map_name = MAPS[idx]
            else:
                continue
        for cat, pts in block.items():
            if cat in _META_KEYS or not isinstance(pts, list):
                continue
            for pt in pts:
                if not isinstance(pt, dict) or "c" not in pt:
                    continue
                c = pt["c"]
                if not isinstance(c, (list, tuple)) or len(c) < 2:
                    continue
                if not user_data.coord_valid(c[0], c[1]):
                    continue
                result = user_data.add_point(
                    result, map_name, cat, c[0], c[1], pt.get("d", ""))
    return result
