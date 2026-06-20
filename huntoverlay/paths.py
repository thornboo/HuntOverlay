"""Filesystem paths and JSON read/write.

This module does touch the filesystem (that is its job), but it has no Qt
or network dependency. Runtime files live in %LOCALAPPDATA%\\HuntOverlay.
"""

import json
import os
import shutil
import sys
import tempfile


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


def _atomic_temp_path(path: str):
    directory = os.path.dirname(os.path.abspath(path))
    basename = os.path.basename(path)
    return tempfile.mkstemp(prefix=f".{basename}.", suffix=".tmp", dir=directory)


def atomic_write_bytes(path: str, data: bytes) -> None:
    """Write bytes by replacing the target only after the full temp write."""
    tmp = None
    try:
        fd, tmp = _atomic_temp_path(path)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass


def atomic_write_text(path: str, text: str) -> None:
    """Write text by replacing the target only after the full temp write."""
    tmp = None
    try:
        fd, tmp = _atomic_temp_path(path)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass


def save_json(path: str, obj) -> None:
    try:
        atomic_write_text(path, json.dumps(obj, indent=2))
    except OSError:
        pass
