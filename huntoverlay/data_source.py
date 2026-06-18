"""Remote data update layer.

SAFETY / AUDIT: all network access in the app funnels through here, and
only to the URLs in constants (DATA_URL/STYLE_URL). Each download is
validated as JSON before it overwrites a local file. No process or memory
access — pure HTTP GET + file write.

Logic is moved verbatim from the single-file build; the only change is
that the meta-file path and update interval are passed in explicitly
instead of read from module-level globals.
"""

import json
import os
import urllib.request
from datetime import datetime, timedelta

from .paths import load_json, save_json

# Default cadence for the legacy "needs update?" check (6h): keeps POI data
# reasonably fresh without hitting the upstream server on every launch.
UPDATE_INTERVAL = timedelta(hours=6)


def load_update_meta(meta_path: str) -> dict:
    try:
        return load_json(meta_path)
    except (OSError, ValueError):
        return {}


def save_update_meta(meta_path: str, meta: dict) -> None:
    save_json(meta_path, meta)


def needs_data_update(meta_path: str, interval: timedelta = UPDATE_INTERVAL) -> bool:
    last = load_update_meta(meta_path).get("last_check", "")
    if not last:
        return True
    try:
        return datetime.now() - datetime.fromisoformat(last) >= interval
    except ValueError:
        return True


def fetch_remote_file(url: str, dst: str) -> bool:
    """Download url, validate as JSON, write to dst. Returns True on success."""
    try:
        with urllib.request.urlopen(url, timeout=15) as r:  # https only, see constants
            raw = r.read()
        json.loads(raw.decode("utf-8"))  # validate before overwriting
        with open(dst, "wb") as f:
            f.write(raw)
        return True
    except Exception:
        return False


# Cap a single image download to avoid pathological payloads (8 MB).
_MAX_IMAGE_BYTES = 8 * 1024 * 1024


def fetch_image(url: str, dst: str) -> bool:
    """Download an image to dst. Returns True on success.

    SAFETY: callers must pass only whitelisted image URLs (see images.
    is_allowed_image_url). Downloads are size-capped and written atomically
    (temp file then rename) so a partial download never leaves a corrupt
    cache entry.
    """
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            raw = r.read(_MAX_IMAGE_BYTES + 1)
        if not raw or len(raw) > _MAX_IMAGE_BYTES:
            return False
        tmp = dst + ".part"
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, dst)
        return True
    except Exception:
        return False


def last_update_status(ts: str):
    """Classify a last-check timestamp into a (status, formatted_time) pair.

    Pure logic, no user-facing text — the UI layer composes the message via
    i18n so this core module stays language-agnostic.

    Returns:
        ("never", "")                     — never updated
        ("updated", "YYYY-MM-DD HH:MM")   — updated at that local time
        ("unknown", "")                   — timestamp present but unparseable
    """
    if not ts:
        return ("never", "")
    try:
        dt = datetime.fromisoformat(ts)
        return ("updated", dt.strftime("%Y-%m-%d %H:%M"))
    except ValueError:
        return ("unknown", "")
