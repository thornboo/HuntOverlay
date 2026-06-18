"""Runtime paths and resources resolved at startup.

Centralizes the per-run paths that used to be module-level globals in the
single-file build. ICON is resolved eagerly (cheap, no side effect). The
user data files are exposed via functions so importing this module does
not trigger file copies — call data_path()/style_path() at startup.
"""

import os

from .paths import bd, udir, ensure_user_file

# Icon path: empty string if the bundled icon is missing.
ICON = os.path.join(bd(), "myicon.ico") if os.path.isfile(os.path.join(bd(), "myicon.ico")) else ""

# Paths that do not require copying.
CONFIG_PATH = os.path.join(udir(), "config.json")
META_PATH = os.path.join(udir(), "update_meta.json")
# User-authored POIs; never overwritten by remote data refreshes.
USER_POIS_PATH = os.path.join(udir(), "user_pois.json")
# Cache directory for downloaded POI reference images.
IMG_CACHE_DIR = os.path.join(udir(), "img_cache")


def data_path() -> str:
    """Ensure data.json exists in the user dir and return its path."""
    return ensure_user_file("data.json")


def style_path() -> str:
    """Ensure poiData.json exists in the user dir and return its path."""
    return ensure_user_file("poiData.json")
