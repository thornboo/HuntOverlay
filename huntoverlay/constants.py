"""Static constants and label lookups for HuntOverlay.

Pure data only — no Qt, no ctypes, no I/O. Safe to import anywhere,
including unit tests running without a GUI or Windows.
"""

# Map order is intentionally set to the release order requested.
MAPS = ["Stillwater Bayou", "Lawson Delta", "DeSalle", "Mammon's Gulch"]

CONFIG_VERSION = "1.2.0"
APP_TITLE = "猎杀对决地图覆盖工具"

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
