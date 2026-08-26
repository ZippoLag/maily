from datetime import UTC, datetime
from pathlib import Path

import pytest

from maily.config import Rule, load_config
from maily.models import EmailMessage


def make_message(
    subject: str = "", body: str = "", sender_email: str = ""
) -> EmailMessage:
    return EmailMessage(
        "1",
        "t",
        "",
        sender_email,
        sender_email.split("@")[-1] if sender_email else "",
        subject,
        body,
        datetime.now(UTC),
        True,
        False,
    )


def test_rule_matches_tracks_which_patterns_matched():
    rule = Rule("Action Required", ("verify", "due date", "urgent"))
    message = make_message(subject="Please verify your account")
    assert rule.matches(message) == ("verify",)


def test_rule_matches_records_all_matched_patterns_in_order():
    rule = Rule("Action Required", ("verify", "due date"))
    message = make_message(subject="URGENT: verify due date")
    assert rule.matches(message) == ("verify", "due date")


def test_rule_matches_returns_empty_when_nothing_matches():
    rule = Rule("Action Required", ("verify", "due date"))
    message = make_message(subject="Hello world")
    assert rule.matches(message) == ()


def _write_config(config_dir: Path, body: str) -> None:
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(body)


def test_config_parses_scan_section(tmp_path: Path):
    _write_config(
        tmp_path / ".maily",
        'timezone = "UTC"\n[scan]\ndate_range = "last 30 days"\n'
        'include_read = true\nchunk_size = "week"\n[gmail]\noauth_client_file = ""\n',
    )
    config = load_config(tmp_path / ".maily")
    assert config.scan_date_range == "last 30 days"
    assert config.scan_include_read is True
    assert config.scan_chunk_size == "week"


def test_config_scan_defaults_for_old_configs(tmp_path: Path):
    """Configs without a [scan] section keep working with defaults (migration)."""
    config = load_config(tmp_path / ".maily")
    assert config.scan_date_range is None
    assert config.scan_include_read is False
    assert config.scan_chunk_size == "day"


def test_config_rejects_invalid_scan_date_range(tmp_path: Path):
    _write_config(
        tmp_path / ".maily",
        'timezone = "UTC"\n[scan]\ndate_range = "not a real range"\n'
        '[gmail]\noauth_client_file = ""\n',
    )
    with pytest.raises(ValueError, match="scan.date_range"):
        load_config(tmp_path / ".maily")


def test_config_rejects_invalid_scan_chunk_size(tmp_path: Path):
    _write_config(
        tmp_path / ".maily",
        'timezone = "UTC"\n[scan]\nchunk_size = "hour"\n'
        '[gmail]\noauth_client_file = ""\n',
    )
    with pytest.raises(ValueError, match="scan.chunk_size"):
        load_config(tmp_path / ".maily")


def test_default_config_documents_scan_examples(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    content = (config.home / "config.toml").read_text(encoding="utf-8")
    assert "[scan]" in content
    assert "date_range" in content
    assert "include_read" in content
    assert "chunk_size" in content
