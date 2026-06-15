"""Unit tests for huntoverlay.data_source — meta/update logic, no network."""

import os
from datetime import datetime, timedelta

import pytest

from huntoverlay.data_source import (
    load_update_meta,
    save_update_meta,
    needs_data_update,
    format_last_update,
)


@pytest.mark.unit
def test_load_update_meta_missing_returns_empty(tmp_path):
    assert load_update_meta(os.path.join(tmp_path, "nope.json")) == {}


@pytest.mark.unit
def test_save_then_load_roundtrip(tmp_path):
    p = os.path.join(tmp_path, "meta.json")
    save_update_meta(p, {"last_check": "2026-06-15T10:00:00"})
    assert load_update_meta(p) == {"last_check": "2026-06-15T10:00:00"}


@pytest.mark.unit
def test_needs_update_when_no_meta(tmp_path):
    assert needs_data_update(os.path.join(tmp_path, "absent.json")) is True


@pytest.mark.unit
def test_needs_update_when_stale(tmp_path):
    p = os.path.join(tmp_path, "meta.json")
    old = (datetime.now() - timedelta(hours=48)).isoformat()
    save_update_meta(p, {"last_check": old})
    assert needs_data_update(p, timedelta(hours=24)) is True


@pytest.mark.unit
def test_no_update_when_fresh(tmp_path):
    p = os.path.join(tmp_path, "meta.json")
    recent = datetime.now().isoformat()
    save_update_meta(p, {"last_check": recent})
    assert needs_data_update(p, timedelta(hours=24)) is False


@pytest.mark.unit
def test_needs_update_on_corrupt_timestamp(tmp_path):
    p = os.path.join(tmp_path, "meta.json")
    save_update_meta(p, {"last_check": "not-a-date"})
    assert needs_data_update(p) is True


@pytest.mark.unit
def test_format_last_update():
    assert format_last_update("") == "数据：从未更新"
    assert format_last_update("garbage") == "数据：未知状态"
    out = format_last_update("2026-06-15T14:30:00")
    assert out.startswith("数据已更新：") and "2026-06-15 14:30" in out
