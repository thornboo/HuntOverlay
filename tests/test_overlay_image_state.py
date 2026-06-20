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
        _img_prefetch_queued={url},
    )

    overlay.Overlay._finish_image_download(state, url, True)

    assert state._img_status[url] == "ready"
    assert url not in state._img_failed_at
    assert url not in state._img_inflight
    assert url not in state._img_prefetch_queued


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
        _img_prefetch_queued={url},
    )

    overlay.Overlay._finish_image_download(state, url, False)

    assert state._img_status[url] == "failed"
    assert state._img_failed_at[url] == 42.0
    assert url not in state._img_inflight
    assert url not in state._img_prefetch_queued


@pytest.mark.unit
def test_image_prefetch_finish_clears_queue_and_runs_pending(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    calls = []
    urls = ["https://i.imgur.com/a.png", "https://i.imgur.com/b.png"]
    state = SimpleNamespace(
        game_data=[{"n": "DeSalle"}],
        _img_prefetch_queued=set(urls),
        _image_prefetch_running=True,
        _image_prefetch_pending=True,
        _start_image_prefetch=lambda game_data: calls.append(game_data),
    )

    overlay.Overlay._on_image_prefetch_finished(state, urls)

    assert state._img_prefetch_queued == set()
    assert state._image_prefetch_running is False
    assert state._image_prefetch_pending is False
    assert calls == [state.game_data]


@pytest.mark.unit
def test_hover_uses_image_url(monkeypatch, tmp_path):
    overlay = _load_overlay(monkeypatch, tmp_path)
    state = SimpleNamespace(
        hover={"pt_ref": {"raw": {"u": ["https://i.imgur.com/a.png"]}}},
    )

    assert overlay.Overlay._hover_uses_image_url(state, "https://i.imgur.com/a.png") is True
    assert overlay.Overlay._hover_uses_image_url(state, "https://i.imgur.com/b.png") is False
