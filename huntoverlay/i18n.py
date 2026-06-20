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


# ── General UI strings ────────────────────────────────────────────────────
# Keyed by the English source text (gettext-style). English is "under the
# hood": tr() returns the key itself for language "en" or any missing key, so
# the UI never blanks. Only non-English translations need entries here.
_UI = {
    "zh": {
        # Panel — Types tab
        "Select All": "全选",
        "Deselect All": "全不选",
        "Map:": "地图：",
        "1-4 map switch keys": "1-4 数字键切图",
        "Scale:": "缩放：",
        "Reset Colors": "重置颜色",
        "POIs": "点位",
        # Panel — Keybinds tab
        "Set": "设置",
        "Keybinds": "快捷键",
        # Panel — Settings tab
        "Minimize to system tray": "最小化到系统托盘",
        "Hold Tab to show overlay": "按住 Tab 显示覆盖层",
        "Block Shift+Tab": "屏蔽 Shift+Tab",
        "Panel follows Tab (show/hide with overlay)": "菜单跟随 Tab（与覆盖层一起显示/隐藏）",
        "Reset to Default Config": "恢复默认配置",
        "Open Data Folder": "打开应用数据目录",
        "Data: checking...": "数据：检查中...",
        "Data updated: ": "数据已更新：",
        "Data: never updated": "数据：从未更新",
        "Data: unknown": "数据：未知状态",
        "Refresh Data": "刷新数据",
        "Settings": "设置",
        "Language:": "语言：",
        "Aspect:": "屏幕比例：",
        "Restart to apply the language change.": "重启后语言更改生效。",
        # Overlay — tray / status / errors
        "Restore control panel": "恢复控制面板",
        "Quit": "退出",
        "Control panel minimized to tray": "控制面板已最小化到托盘",
        "Data: updating...": "数据：正在更新...",
        "Updating map data...": "正在更新地图数据...",
        "Downloading images": "正在下载图片",
        "Loading image...": "正在加载图片...",
        "Image unavailable": "图片不可用",
        # Overlay — runtime errors / map title
        "Error": "错误",
        "HuntOverlay is already running.": "HuntOverlay 已在运行。",
        "Missing data.json": "缺少 data.json",
        "Missing poiData.json": "缺少 poiData.json",
        "Unrecognized data.json format": "无法识别 data.json 数据格式",
        "Map": "地图",
        # Dialogs — keybind capture
        "Set keybind: ": "设置快捷键：",
        "Press a key\nHold Ctrl / Alt / Shift if needed\nEsc to cancel":
            "请按下一个按键\n可同时按住 Ctrl / Alt / Shift\nEsc 取消",
        # Dialogs — color picker
        "Pick a Color": "选择颜色",
        "Hue": "色相",
        "Red": "红",
        "Green": "绿",
        "Blue": "蓝",
        "Hex": "十六进制",
        "Presets": "预设颜色",
        "OK": "确定",
        "Cancel": "取消",
        # POI editor
        "POI type:": "点位类型：",
        "Edit POIs": "编辑点位",
        "Ruler": "标尺",
        "Clear Rulers": "清空标尺",
        "Click to set start point": "点击设置起点",
        "Edit Custom POIs": "编辑自定义点位",
        "Category:": "分类：",
        "Description": "描述",
        "Image URLs (comma-separated)": "图片链接（逗号分隔）",
        "Images": "图片",
        "Add": "新增",
        "Pick from Map": "从地图拾取",
        "Delete Selected": "删除选中",
        "Undo": "撤销",
        "Import": "导入",
        "Export": "导出",
        "Copy to Clipboard": "复制到剪贴板",
        "Paste exported data here": "在此粘贴导出的数据",
        "Close": "关闭",
        "Custom points only (official points are read-only)":
            "仅显示自定义点位（官方点位只读）",
        "Invalid coordinates (need 0-4095).": "坐标无效（需 0–4095）。",
        # Boss reference tab
        "Bosses": "首领",
        "Butcher": "屠夫",
        "Spider": "蜘蛛",
        "Assassin": "刺客",
        "Scrapbeak": "废喙",
        "Fire": "火焰",
        "Poison": "毒素",
        "Weak": "弱点",
        "Immune": "免疫",
        "Normal": "一般",
        "Banish time and exact HP vary by patch and are omitted.":
            "净化时间与精确血量随版本变动，故不列出。",
        # Butcher tips
        "Immune to fire — do not waste fire ammo.": "免疫火焰——不要浪费火焰弹药。",
        "Weak to explosives and close-range shotguns.": "弱点是炸药和近距离霰弹枪。",
        "Slow mover; keep distance and lead with explosives.":
            "移动缓慢；保持距离，先用炸药开场。",
        "Enters a rage phase after heavy damage.": "受到重创后进入狂暴阶段。",
        # Spider tips
        "Weak to fire — molotovs, fire ammo, burning lamps.":
            "弱火——燃烧瓶、火焰弹药、燃烧的油灯。",
        "Immune to poison; antidote counters its poison spit.":
            "免疫毒素；解毒针可应对它的毒液喷射。",
        "Dynamite is effective, especially while it clings to walls/ceiling.":
            "炸药很有效，尤其在它攀附墙壁/天花板时。",
        "Can be bled out at low health.": "低血量时可被流血效果消耗致死。",
        # Assassin tips
        "Weak to fire — burns even while split into a swarm.":
            "弱火——即使分裂成蜂群也会持续燃烧。",
        "Use heavy melee (axe/hammer) during its swarm form.":
            "蜂群形态时用重型近战（斧/锤）。",
        "Watch its teleport pattern; strike when it reforms.":
            "观察它的传送规律；在它重组时攻击。",
        # Scrapbeak tips
        "Scrap armor blocks part of firearm damage.": "废甲会抵挡部分枪械伤害。",
        "Heavy melee bypasses the armor; weaker after losing armor pieces.":
            "重型近战可无视护甲；掉甲后更脆弱。",
        "Avoid his barbed wire — it slows and damages you.":
            "避开它的倒刺铁丝网——会减速并造成伤害。",
    },
}


def tr(text: str) -> str:
    """Translate a UI string by its English source text.

    Returns the current language's translation, or the English text itself
    for 'en' / unknown keys (so the UI never shows a blank).
    """
    lang_table = _UI.get(_current)
    if lang_table and text in lang_table:
        return lang_table[text]
    return text
