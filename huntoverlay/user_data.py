"""User-authored POI storage and merge logic.

SAFETY / DATA INTEGRITY: user points live in their own file (user_pois.json)
and are NEVER written into data.json, so a remote data refresh can never
overwrite them. This module is pure logic + JSON I/O — no Qt, no network.

Stored schema (mirrors data.json point shape so the render pipeline reuses
it unchanged):

    {
      "version": 1,
      "maps": {
        "<map English name>": {
          "<category>": [ {"c": [x, y], "d": "note", "_user": true}, ... ]
        }
      }
    }
"""

import copy

from .paths import load_json, save_json

USER_POIS_VERSION = 1

# Coordinate grid bounds (Hunt maps are a 4096x4096 grid: 0..4095).
COORD_MIN = 0
COORD_MAX = 4095


def empty_user_pois() -> dict:
    return {"version": USER_POIS_VERSION, "maps": {}}


def coord_valid(x, y) -> bool:
    """True if both coordinates are numbers within the 0..4095 grid."""
    try:
        xf, yf = float(x), float(y)
    except (TypeError, ValueError):
        return False
    return COORD_MIN <= xf <= COORD_MAX and COORD_MIN <= yf <= COORD_MAX


def get_points(data: dict, map_name: str, category: str) -> list:
    """User points for a map+category; empty list if absent. Read-only view."""
    if not isinstance(data, dict):
        return []
    return list(data.get("maps", {}).get(map_name, {}).get(category, []))


def add_point(data: dict, map_name: str, category: str, x, y, desc: str = "",
              images=None) -> dict:
    """Return a NEW data dict with one user point appended. Does not mutate input.

    Raises ValueError if coordinates are out of range. `images` is an optional
    list of image URLs, stored under "u" to match the data.json point shape.
    """
    if not coord_valid(x, y):
        raise ValueError(f"坐标超出范围（需 {COORD_MIN}–{COORD_MAX}）：({x}, {y})")

    result = copy.deepcopy(data) if isinstance(data, dict) else empty_user_pois()
    result.setdefault("version", USER_POIS_VERSION)
    maps = result.setdefault("maps", {})
    cats = maps.setdefault(map_name, {})
    points = cats.setdefault(category, [])

    point = {"c": [int(round(float(x))), int(round(float(y)))], "_user": True}
    if desc:
        point["d"] = str(desc)
    if images:
        urls = [str(u).strip() for u in images if str(u).strip()]
        if urls:
            point["u"] = urls
    points.append(point)
    return result


def remove_point(data: dict, map_name: str, category: str, index: int) -> dict:
    """Return a NEW data dict with the point at index removed. Out-of-range
    index is a no-op (returns an unchanged copy)."""
    result = copy.deepcopy(data) if isinstance(data, dict) else empty_user_pois()
    points = result.get("maps", {}).get(map_name, {}).get(category, [])
    if 0 <= index < len(points):
        del points[index]
    return result


def merge_into_points(remote_points: list, user_points: list) -> list:
    """Combine remote (read-only) and user points for rendering.

    Both are lists of point dicts ({"c": [x, y], ...}); the result is a new
    list, remote first then user, so user points draw on top.
    """
    out = list(remote_points) if isinstance(remote_points, list) else []
    if isinstance(user_points, list):
        out.extend(user_points)
    return out


def load_user_pois(path: str) -> dict:
    """Load user_pois.json; return an empty structure if missing/corrupt."""
    try:
        data = load_json(path)
    except (OSError, ValueError):
        return empty_user_pois()
    if not isinstance(data, dict) or "maps" not in data:
        return empty_user_pois()
    return data


def save_user_pois(path: str, data: dict) -> None:
    save_json(path, data)
