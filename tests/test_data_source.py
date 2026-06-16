"""Unit tests for huntoverlay.data_source — meta/update logic, no network."""

import os
from datetime import datetime, timedelta

import pytest

from huntoverlay.data_source import (
    load_update_meta,
    save_update_meta,
    needs_data_update,
    last_update_status,
    UPDATE_INTERVAL,
)


@pytest.mark.unit
def test_default_update_interval_is_6h():
    # Locked at 6h: fresh enough without hammering upstream on every launch.
    assert UPDATE_INTERVAL == timedelta(hours=6)


@pytest.mark.unit
def test_default_interval_used_when_not_passed(tmp_path):
    # 5h-old check should NOT trigger under the 6h default.
    p = os.path.join(tmp_path, "meta.json")
    five_h_ago = (datetime.now() - timedelta(hours=5)).isoformat()
    save_update_meta(p, {"last_check": five_h_ago})
    assert needs_data_update(p) is False
    # 7h-old check SHOULD trigger under the 6h default.
    seven_h_ago = (datetime.now() - timedelta(hours=7)).isoformat()
    save_update_meta(p, {"last_check": seven_h_ago})
    assert needs_data_update(p) is True



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
def test_last_update_status():
    # Pure status code + formatted time; no user-facing text here.
    assert last_update_status("") == ("never", "")
    assert last_update_status("garbage") == ("unknown", "")
    status, when = last_update_status("2026-06-15T14:30:00")
    assert status == "updated"
    assert when == "2026-06-15 14:30"
