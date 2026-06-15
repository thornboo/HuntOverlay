"""Static constants and label lookups for HuntOverlay.

Pure data only — no Qt, no ctypes, no I/O. Safe to import anywhere,
including unit tests running without a GUI or Windows.
"""

# Map order is intentionally set to the release order requested.
MAPS = ["Stillwater Bayou", "Lawson Delta", "DeSalle", "Mammon's Gulch"]

CONFIG_VERSION = "1.2.0"
APP_TITLE = "猎杀对决地图覆盖工具"

CATEGORY_LABELS_ZH = {
    "possible_xp": "潜在经验点",
    "spawns": "出生点",
    "armories": "军械库",
    "towers": "狩猎塔",
    "big_towers": "瞭望塔",
    "workbenches": "工作台",
    "wild_targets": "野外目标",
    "brutes": "重型怪物",
    "beetles": "甲虫",
    "easter_eggs": "彩蛋",
    "melee_weapons": "近战武器",
    "cash_registers": "收银机",
}

ACTION_LABELS_ZH = {
    "toggle_master": "总开关",
    "toggle_overlay": "显示/隐藏覆盖层",
    "hide_overlay": "隐藏覆盖层",
    "map_1": "地图 1  静水河口",
    "map_2": "地图 2  劳森三角洲",
    "map_3": "地图 3  德萨莱",
    "map_4": "地图 4  玛门峡谷",
    "hide_hovered": "隐藏鼠标指向点位",
}

# Display names for maps. The English names in MAPS remain the canonical keys
# used for config storage, data.json lookup, and the per-map point cache.
# These labels are only for what the user sees in the UI.
MAP_LABELS_ZH = {
    "Stillwater Bayou": "静水河口",
    "Lawson Delta": "劳森三角洲",
    "DeSalle": "德萨莱",
    "Mammon's Gulch": "玛门峡谷",
}

# Win32 virtual key codes used by defaults and modifier detection.
VK_TAB = 0x09
VK_H = 0x48
VK_BT = 0xC0
VK1, VK2, VK3, VK4 = 0x31, 0x32, 0x33, 0x34

VK_ESC = 0x1B
VK_DELETE = 0x2E
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12

DEFAULT_HIDDEN_POSSIBLE_XP = [
    "armories:1508:2096",
    "big_towers:1320:3328",
]

# Remote data sources. All network access is restricted to these URLs.
DATA_URL = "https://hunt.kamille.ovh/maps/data.json"
STYLE_URL = "https://hunt.kamille.ovh/maps/poiData.json"


def category_label(category: str, fallback: str) -> str:
    return CATEGORY_LABELS_ZH.get(category, str(fallback))


def map_display(name: str) -> str:
    """English canonical map name -> Chinese display label (falls back to the name)."""
    return MAP_LABELS_ZH.get(name, str(name))
