"""Lightweight multi-language layer for HuntOverlay (step 1: data labels).

Design (Plan C, step 1): the structured label tables that used to live in
constants.py (map names, POI categories, hotkey actions) move here as
per-language tables keyed by a stable canonical key. A module-level current
language drives lookups, with English as the ultimate fallback so the UI
never shows a blank.

This step is pure logic — no Qt — and covers the already-structured labels.
Scattered UI strings in the widgets (e.g. button captions) are deferred to
step 2, which touches Qt code and needs on-device verification.

Supported languages: zh (current default, preserves existing behavior) and
en. More can be added by extending the tables.
"""

# (code, display name shown in a future language selector, in its own script)
LANGUAGES = [
    ("zh", "中文"),
    ("en", "English"),
]

_CODES = {c for c, _ in LANGUAGES}

DEFAULT_LANG = "zh"

# Module-level current language. Kept simple (single-process GUI app).
_current = DEFAULT_LANG


def available_languages():
    """List of (code, display_name) for a language selector."""
    return list(LANGUAGES)


def get_language() -> str:
    return _current


def set_language(code: str) -> None:
    """Set the active language; ignores unknown codes (keeps current)."""
    global _current
    if code in _CODES:
        _current = code


# ── Map names ─────────────────────────────────────────────────────────────
# Keyed by the canonical English map name (also the data.json / config key).
_MAP_LABELS = {
    "Stillwater Bayou": {"zh": "静水河口", "en": "Stillwater Bayou"},
    "Lawson Delta":     {"zh": "劳森三角洲", "en": "Lawson Delta"},
    "DeSalle":          {"zh": "德萨莱", "en": "DeSalle"},
    "Mammon's Gulch":   {"zh": "玛门峡谷", "en": "Mammon's Gulch"},
}

# ── POI category labels ───────────────────────────────────────────────────
_CATEGORY_LABELS = {
    "possible_xp":    {"zh": "潜在经验点", "en": "Possible XP Location"},
    "spawns":         {"zh": "出生点", "en": "Spawns"},
    "armories":       {"zh": "军械库", "en": "Armories"},
    "towers":         {"zh": "狩猎塔", "en": "Hunting Towers"},
    "big_towers":     {"zh": "瞭望塔", "en": "Watch Towers"},
    "workbenches":    {"zh": "工作台", "en": "Workbenches"},
    "wild_targets":   {"zh": "野外目标", "en": "Wild Targets"},
    "brutes":         {"zh": "重型怪物", "en": "Brutes"},
    "beetles":        {"zh": "甲虫", "en": "Beetles"},
    "easter_eggs":    {"zh": "彩蛋", "en": "Easter Eggs"},
    "melee_weapons":  {"zh": "近战武器", "en": "Melee Weapons"},
    "cash_registers": {"zh": "收银机", "en": "Cash Registers"},
}

# ── Hotkey action labels ──────────────────────────────────────────────────
_ACTION_LABELS = {
    "toggle_master":  {"zh": "总开关", "en": "Toggle master"},
    "toggle_overlay": {"zh": "显示/隐藏覆盖层", "en": "Toggle overlay"},
    "hide_overlay":   {"zh": "隐藏覆盖层", "en": "Hide overlay"},
    "map_1":          {"zh": "地图 1  静水河口", "en": "Map 1  Stillwater"},
    "map_2":          {"zh": "地图 2  劳森三角洲", "en": "Map 2  Lawson"},
    "map_3":          {"zh": "地图 3  德萨莱", "en": "Map 3  DeSalle"},
    "map_4":          {"zh": "地图 4  玛门峡谷", "en": "Map 4  Mammon"},
    "hide_hovered":   {"zh": "隐藏鼠标指向点位", "en": "Hide hovered POI"},
}


def _lookup(table: dict, key: str, fallback: str) -> str:
    entry = table.get(key)
    if not entry:
        return fallback
    # current language → English → provided fallback
    return entry.get(_current) or entry.get("en") or fallback


def map_display(name: str) -> str:
    """Canonical English map name -> label in the current language.

    Falls back to the name itself for unknown maps (unchanged behavior).
    """
    return _lookup(_MAP_LABELS, name, str(name))


def category_label(category: str, fallback: str) -> str:
    """POI category key -> label in the current language; fallback if unknown."""
    return _lookup(_CATEGORY_LABELS, category, str(fallback))


def action_label(action: str, fallback: str = "") -> str:
    """Hotkey action key -> label in the current language."""
    return _lookup(_ACTION_LABELS, action, fallback or action)


def action_labels() -> dict:
    """Mapping of action key -> current-language label (replaces ACTION_LABELS_ZH)."""
    return {k: _lookup(_ACTION_LABELS, k, k) for k in _ACTION_LABELS}
