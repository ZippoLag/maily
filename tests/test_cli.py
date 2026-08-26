import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

import maily.tui
from maily import cli
from maily.cli import build_parser, main, render_human, run_scan
from maily.config import load_config


def test_human_output_shows_action_required_email_details():
    """Test that Action Required emails show subject and sender in human-readable output"""
    output = render_human(
        {
            "status": "completed",
            "messages": [
                {
                    "subject": "Important Meeting",
                    "sender_email": "boss@example.com",
                    "body": "Please attend",
                    "category": "Action Required",
                },
                {
                    "subject": "Newsletter",
                    "sender_email": "news@example.com",
                    "body": "Daily news",
                    "category": "Newsletters",
                },
            ],
            "counts": {"Action Required": 1, "Newsletters": 1},
            "categories": {
                "Action Required": [
                    {
                        "subject": "Important Meeting",
                        "sender_email": "boss@example.com",
                        "body": "Please attend",
                    }
                ],
                "Newsletters": [
                    {
                        "subject": "Newsletter",
                        "sender_email": "news@example.com",
                        "body": "Daily news",
                    }
                ],
            },
            "historical_counts": {"deferred": False},
            "errors": [],
        }
    )
    assert "Important Meeting (boss@example.com)" in output
    assert "Action Required: 1" in output
    assert "Newsletters: 1" in output


def test_human_output_handles_empty_subject_in_action_required():
    """Test that empty subject is displayed as '(no subject)' in Action Required emails"""
    output = render_human(
        {
            "status": "completed",
            "messages": [
                {
                    "subject": "",
                    "sender_email": "test@example.com",
                    "body": "Test",
                    "category": "Action Required",
                },
            ],
            "counts": {"Action Required": 1},
            "categories": {
                "Action Required": [
                    {"subject": "", "sender_email": "test@example.com", "body": "Test"}
                ]
            },
            "historical_counts": {"deferred": False},
            "errors": [],
        }
    )
    assert "(no subject) (test@example.com)" in output


def test_human_output_no_action_required_shows_only_counts():
    """Test that categories without Action Required only show counts"""
    output = render_human(
        {
            "status": "completed",
            "messages": [
                {
                    "subject": "Newsletter",
                    "sender_email": "news@example.com",
                    "body": "Daily news",
                    "category": "Newsletters",
                },
            ],
            "counts": {"Newsletters": 1, "Work": 0},
            "categories": {
                "Newsletters": [
                    {
                        "subject": "Newsletter",
                        "sender_email": "news@example.com",
                        "body": "Daily news",
                    }
                ],
                "Work": [],
            },
            "historical_counts": {"deferred": False},
            "errors": [],
        }
    )
    assert "Newsletters: 1" in output
    assert "Work: 0" in output
    # Should NOT have email details for non-Action Required categories
    assert "Newsletter (news@example.com)" not in output


def test_human_output_other_categories_unchanged():
    """Test that existing behavior for other categories is unchanged"""
    output = render_human(
        {
            "status": "completed",
            "messages": [],
            "counts": {"Work": 5, "Personal": 3},
            "categories": {},
            "historical_counts": {"deferred": False},
            "errors": [],
        }
    )
    assert "Work: 5" in output
    assert "Personal: 3" in output
    assert "Scan: completed" in output


def test_build_parser_accepts_commands():
    parser = build_parser()
    assert parser.parse_args(["scan", "--json-format"]).command == "scan"
    assert parser.parse_args(["tui"]).command == "tui"
    assert parser.parse_args(["init"]).command == "init"


def test_version_flag_exits_zero(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert "maily" in capsys.readouterr().out


def test_run_scan_without_oauth_client_fails_cleanly(tmp_path, capsys, monkeypatch):
    # Credential store is available, but no OAuth client file is configured.
    monkeypatch.setattr(cli, "CredentialStore", lambda: SimpleNamespace())
    config = load_config(tmp_path / "home")
    assert run_scan(config, as_json=True) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "failed"
    assert "oauth_client_file" in payload["errors"][0]


def test_run_scan_success_payload(tmp_path, capsys, monkeypatch):
    config = replace(
        load_config(tmp_path / "home"), oauth_client_file=tmp_path / "client.json"
    )
    monkeypatch.setattr(cli, "CredentialStore", lambda: SimpleNamespace())
    monkeypatch.setattr(
        cli, "authenticate", lambda *a, **k: (SimpleNamespace(), "me@example.com")
    )
    monkeypatch.setattr(cli, "OllamaProvider", lambda *a, **k: SimpleNamespace())
    monkeypatch.setattr(
        cli,
        "scan",
        lambda *a, **k: SimpleNamespace(
            as_dict=lambda: {
                "status": "completed",
                "messages": [],
                "categories": {},
                "counts": {},
                "historical_counts": {"deferred": False},
                "errors": [],
            }
        ),
    )
    monkeypatch.setattr(cli, "Classifier", lambda *a, **k: SimpleNamespace())
    assert run_scan(config, as_json=True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["account"] == "me@example.com"


def test_main_init(tmp_path, capsys):
    assert main(["--home", str(tmp_path / "home"), "init"]) == 0
    assert "State initialized" in capsys.readouterr().out


def test_main_tui_friendly_error(tmp_path, capsys, monkeypatch):
    def boom(config, as_json):
        raise RuntimeError("Install maily with the 'tui' extra to use the TUI")

    monkeypatch.setattr(maily.tui, "run_tui", boom)
    assert main(["--home", str(tmp_path / "home"), "tui"]) == 1
    assert "Install maily with the 'tui' extra" in capsys.readouterr().err


def test_main_scan_delegates(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "run_scan", lambda config, as_json: 3)
    assert main(["--home", str(tmp_path / "home"), "scan"]) == 3
