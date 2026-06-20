"""Unit tests for filesystem JSON helpers."""

import json

import pytest

from huntoverlay import paths


@pytest.mark.unit
def test_save_json_preserves_existing_file_when_replace_fails(monkeypatch, tmp_path):
    dst = tmp_path / "config.json"
    dst.write_text('{"old": true}', encoding="utf-8")

    def fail_replace(_src, _dst):
        raise OSError("replace failed")

    monkeypatch.setattr(paths.os, "replace", fail_replace)

    paths.save_json(str(dst), {"old": False})

    assert json.loads(dst.read_text(encoding="utf-8")) == {"old": True}
    assert list(tmp_path.glob(".config.json.*.tmp")) == []
