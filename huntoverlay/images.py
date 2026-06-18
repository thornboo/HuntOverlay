"""POI reference-image cache logic.

SAFETY / AUDIT: image downloads go to imgur (i.imgur.com), the host the
community data uses. URL collection and cache-path mapping are pure logic
(here); the actual HTTP GET lives in data_source so all network access stays
in one auditable place.

Cache layout: each image URL maps to a file named by a hash of the URL plus
its original extension, under IMG_CACHE_DIR. This avoids unsafe filenames and
de-duplicates identical URLs.
"""

import hashlib
import os
from urllib.parse import urlparse

# Only these hosts are allowed for image downloads (whitelist).
ALLOWED_IMAGE_HOSTS = {"i.imgur.com", "imgur.com"}

_ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def is_allowed_image_url(url: str) -> bool:
    """True if the URL is http(s) and on an allowed image host."""
    try:
        p = urlparse(str(url))
    except (ValueError, TypeError):
        return False
    return p.scheme in ("http", "https") and p.netloc.lower() in ALLOWED_IMAGE_HOSTS


def cache_filename(url: str) -> str:
    """Deterministic cache filename for a URL: <sha1>.<ext>.

    Extension comes from the URL path if it is a known image type, else .img.
    """
    h = hashlib.sha1(str(url).encode("utf-8")).hexdigest()
    ext = os.path.splitext(urlparse(str(url)).path)[1].lower()
    if ext not in _ALLOWED_EXT:
        ext = ".img"
    return f"{h}{ext}"


def cache_path(cache_dir: str, url: str) -> str:
    """Absolute cache path for a URL inside cache_dir."""
    return os.path.join(cache_dir, cache_filename(url))


def collect_image_urls(game_data) -> list:
    """Return the de-duplicated list of allowed image URLs found in game_data.

    Scans every point's "u" list across all maps/categories. Order is stable
    (first-seen) so downloads are deterministic.
    """
    seen = set()
    out = []
    if not isinstance(game_data, list):
        return out
    for block in game_data:
        if not isinstance(block, dict):
            continue
        for key, val in block.items():
            if not isinstance(val, list):
                continue
            for pt in val:
                if not isinstance(pt, dict):
                    continue
                urls = pt.get("u")
                if not isinstance(urls, list):
                    continue
                for u in urls:
                    if u in seen:
                        continue
                    seen.add(u)
                    if is_allowed_image_url(u):
                        out.append(u)
    return out


def missing_images(cache_dir: str, urls) -> list:
    """Subset of urls not yet present in the cache (incremental download)."""
    out = []
    for u in urls:
        if not os.path.isfile(cache_path(cache_dir, u)):
            out.append(u)
    return out


def cleanup_partials(cache_dir: str) -> int:
    """Delete leftover '.part' temp files from interrupted downloads.

    Returns the number removed. Safe to call anytime: completed images use
    their final name, so removing '.part' files never touches valid cache.
    """
    removed = 0
    if not os.path.isdir(cache_dir):
        return 0
    for name in os.listdir(cache_dir):
        if name.endswith(".part"):
            try:
                os.remove(os.path.join(cache_dir, name))
                removed += 1
            except OSError:
                pass
    return removed
