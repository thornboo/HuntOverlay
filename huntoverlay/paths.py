"""Filesystem paths and JSON read/write.

This module does touch the filesystem (that is its job), but it has no Qt
or network dependency. Runtime files live in %LOCALAPPDATA%\\HuntOverlay.
"""

import json
import os
import shutil
import sys


def bd() -> str:
    """Base resource directory.

    - Frozen (PyInstaller): sys._MEIPASS, where --add-data files are unpacked.
    - Source run: the project root (parent of this huntoverlay/ package),
      which is where data.json / poiData.json / myicon.ico live.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return meipass
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def udir() -> str:
    """User data directory; created on first access."""
    p = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "HuntOverlay")
    os.makedirs(p, exist_ok=True)
    return p


def ensure_user_file(filename: str) -> str:
    """
    Ensure a file exists in %LOCALAPPDATA%\\HuntOverlay by copying from
    bundled resources (bd()). Returns the user file path.
    """
    dst = os.path.join(udir(), filename)
    if os.path.isfile(dst):
        return dst

    src = os.path.join(bd(), filename)
    if os.path.isfile(src):
        try:
            shutil.copyfile(src, dst)
        except OSError:
            pass

    return dst


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, obj) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(obj, indent=2))
    except OSError:
        pass
