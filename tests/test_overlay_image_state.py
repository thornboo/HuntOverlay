"""Unit tests for overlay image download state transitions."""

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_overlay(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    sys.modules.pop("huntoverlay.overlay", None)
    sys.modules.pop("huntoverlay.runtime", None)
    return importlib.import_module("huntoverlay.overlay")


@pytest.mark.unit
def test_finish_image_download_marks_ready_and_clears_inflight(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    monkeypatch.setattr(overlay, "IMG_CACHE_DIR", str(cache_dir))

    url = "https://i.imgur.com/a.png"
    path = overlay._images.cache_path(str(cache_dir), url)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\nrest")
    state = SimpleNamespace(
        _img_status={},
        _img_failed_at={url: 10.0},
        _img_inflight={url},
    )

    overlay.Overlay._finish_image_download(state, url, True)

    assert state._img_status[url] == "ready"
    assert url not in state._img_failed_at
    assert url not in state._img_inflight


@pytest.mark.unit
def test_finish_image_download_marks_failed_and_clears_inflight(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    monkeypatch.setattr(overlay, "IMG_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(overlay.time, "monotonic", lambda: 42.0)

    url = "https://i.imgur.com/a.png"
    state = SimpleNamespace(
        _img_status={},
        _img_failed_at={},
        _img_inflight={url},
    )

    overlay.Overlay._finish_image_download(state, url, False)

    assert state._img_status[url] == "failed"
    assert state._img_failed_at[url] == 42.0
    assert url not in state._img_inflight
