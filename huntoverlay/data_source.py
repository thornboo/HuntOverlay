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
import urllib.request
from datetime import datetime, timedelta

from .paths import load_json, save_json

# Default cadence for the legacy "needs update?" check (24h).
UPDATE_INTERVAL = timedelta(hours=24)


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


def format_last_update(ts: str) -> str:
    if not ts:
        return "数据：从未更新"
    try:
        dt = datetime.fromisoformat(ts)
        return "数据已更新：" + dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return "数据：未知状态"
