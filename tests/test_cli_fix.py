"""Tests for OAuth file detection and maily fix command."""

import sqlite3
from pathlib import Path

from dataclasses import replace

from maily.cli import resolve_oauth_client_file, run_fix
from maily.config import load_config


def _make_config(tmp_path):
    """Create a config pointing at tmp_path."""
    return load_config(tmp_path / ".maily")


def _make_oauth_file(
    tmp_path, name="client_secret_abc123.apps.googleusercontent.com.json"
):
    """Create a fake OAuth client file."""
    path = tmp_path / ".maily" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"installed": {"client_id": "test"}}')
    return path


# ── resolve_oauth_client_file ──────────────────────────────────────


def test_resolve_uses_configured_path_when_exists(tmp_path):
    """When config points to a real file, use it directly."""
    config = _make_config(tmp_path)
    oauth_file = _make_oauth_file(tmp_path)
    # Patch config to point to the file
    config = replace(config, oauth_client_file=oauth_file)
    result = resolve_oauth_client_file(config)
    assert result == oauth_file


def test_resolve_falls_back_to_glob_when_configured_missing(tmp_path):
    """When config points to a missing file, auto-detect in config.home."""
    config = _make_config(tmp_path)
    oauth_file = _make_oauth_file(tmp_path)
    # Config points to a non-existent path
    config = replace(config, oauth_client_file=Path("/nonexistent/file.json"))
    result = resolve_oauth_client_file(config)
    assert result == oauth_file


def test_resolve_auto_detects_when_no_config(tmp_path):
    """When config has no oauth_client_file, auto-detect via glob."""
    config = _make_config(tmp_path)
    oauth_file = _make_oauth_file(tmp_path)
    assert config.oauth_client_file is None
    result = resolve_oauth_client_file(config)
    assert result == oauth_file


def test_resolve_picks_first_sorted_candidate(tmp_path):
    """When multiple OAuth files exist, pick the first alphabetically."""
    config = _make_config(tmp_path)
    _make_oauth_file(tmp_path, "a_secret.apps.googleusercontent.com.json")
    _make_oauth_file(tmp_path, "b_secret.apps.googleusercontent.com.json")
    result = resolve_oauth_client_file(config)
    assert result.name == "a_secret.apps.googleusercontent.com.json"


def test_resolve_raises_when_nothing_found(tmp_path):
    """When nothing exists, raise ValueError with guidance."""
    config = _make_config(tmp_path)
    try:
        resolve_oauth_client_file(config)
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "No *.apps.googleusercontent.com.json" in str(exc)
        assert "maily init" in str(exc)


def test_resolve_raises_when_configured_path_missing_no_fallback(tmp_path):
    """When config has a path but no file in home either, raise with both messages."""
    config = _make_config(tmp_path)
    config = replace(config, oauth_client_file=Path("/nonexistent/file.json"))
    try:
        resolve_oauth_client_file(config)
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "does not exist" in str(exc)
        assert "No *.apps.googleusercontent.com.json" in str(exc)


# ── run_fix ────────────────────────────────────────────────────────


def test_run_fix_creates_missing_logs_dir(tmp_path):
    """run_fix creates the logs directory if missing."""
    config = _make_config(tmp_path)
    logs_dir = config.home / "logs"
    assert not logs_dir.exists()
    result = run_fix(config)
    assert result == 0
    assert logs_dir.exists()


def test_run_fix_reports_oauth_status(tmp_path):
    """run_fix reports when OAuth file is found or missing."""
    config = _make_config(tmp_path)
    _make_oauth_file(tmp_path)
    result = run_fix(config)
    assert result == 0
