import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

import maily.tui
from maily import cli
from maily.cli import (
    build_parser,
    main,
    render_human,
    resolve_scan_bounds,
    run_scan,
)
from maily.config import load_config
from maily.db import Database


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


def test_scan_parser_accepts_verbose_debug_flags():
    parser = build_parser()
    assert parser.parse_args(["scan", "--verbose"]).verbose is True
    assert parser.parse_args(["scan", "--debug"]).debug is True
    assert parser.parse_args(["scan"]).verbose is False
    assert parser.parse_args(["scan"]).debug is False


def test_scan_parser_accepts_historical_args():
    parser = build_parser()
    args = parser.parse_args(
        [
            "scan",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-31",
            "--last",
            "7days",
            "--include-read",
            "--chunk-size",
            "week",
        ]
    )
    assert args.start_date == "2024-01-01"
    assert args.end_date == "2024-01-31"
    assert args.last == "7days"
    assert args.include_read is True
    assert args.chunk_size == "week"


def test_scan_parser_rejects_invalid_chunk_size():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["scan", "--chunk-size", "hour"])


def test_resolve_scan_bounds_defaults_to_today(tmp_path):
    config = load_config(tmp_path / "home")
    start, end = resolve_scan_bounds(config, None, None, None)
    today_start, today_end = config.local_today_bounds()
    assert start == today_start
    assert end == today_end


def test_resolve_scan_bounds_start_date_only(tmp_path):
    config = load_config(tmp_path / "home")
    start, end = resolve_scan_bounds(config, "2024-01-01", None, None)
    assert start.isoformat().startswith("2024-01-01")
    today_end = config.local_today_bounds()[1]
    assert end == today_end


def test_resolve_scan_bounds_explicit_range(tmp_path):
    config = load_config(tmp_path / "home")
    start, end = resolve_scan_bounds(config, "2024-01-01", "2024-01-31", None)
    assert start.isoformat().startswith("2024-01-01")
    assert end.isoformat().startswith("2024-01-31")


def test_resolve_scan_bounds_last_relative(tmp_path):
    from datetime import UTC, datetime, timedelta

    config = load_config(tmp_path / "home")
    start, end = resolve_scan_bounds(config, None, None, "7days")
    now = datetime.now(UTC)
    assert start.date() == (now - timedelta(days=7)).date()
    assert end.date() == now.date()
    assert end > start


def test_run_scan_passes_historical_args_through(tmp_path, capsys, monkeypatch):
    config = replace(
        load_config(tmp_path / "home"), oauth_client_file=tmp_path / "client.json"
    )
    monkeypatch.setattr(cli, "CredentialStore", lambda: SimpleNamespace())
    monkeypatch.setattr(
        cli, "authenticate", lambda *a, **k: (SimpleNamespace(), "me@example.com")
    )
    monkeypatch.setattr(cli, "OllamaProvider", lambda *a, **k: SimpleNamespace())
    monkeypatch.setattr(cli, "Classifier", lambda *a, **k: SimpleNamespace())
    captured = {}

    def fake_scan(
        gmail_client,
        database,
        classifier,
        start,
        end,
        include_read=False,
        chunk_size="day",
        progress_callback=None,
        batch_size=100,
        **kwargs,
    ):
        captured["include_read"] = include_read
        captured["chunk_size"] = chunk_size
        captured["start"] = start
        captured["end"] = end
        return SimpleNamespace(
            as_dict=lambda: {
                "status": "completed",
                "messages": [],
                "categories": {},
                "counts": {},
                "historical_counts": {"deferred": False},
                "errors": [],
            }
        )

    monkeypatch.setattr(cli, "scan", fake_scan)
    assert (
        run_scan(
            config,
            as_json=True,
            start_date="2024-01-01",
            end_date="2024-01-31",
            include_read=True,
            chunk_size="week",
        )
        == 0
    )
    capsys.readouterr()
    assert captured["include_read"] is True
    assert captured["chunk_size"] == "week"
    assert captured["start"].isoformat().startswith("2024-01-01")
    assert captured["end"].isoformat().startswith("2024-01-31")


def test_run_scan_uses_config_scan_defaults(tmp_path, capsys, monkeypatch):
    from datetime import UTC, datetime, timedelta

    config_dir = tmp_path / "home"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(
        'timezone = "UTC"\n[scan]\ninclude_read = true\n'
        'chunk_size = "week"\ndate_range = "last 7 days"\n'
        '[gmail]\noauth_client_file = ""\n'
    )
    config = replace(
        load_config(config_dir), oauth_client_file=tmp_path / "client.json"
    )
    monkeypatch.setattr(cli, "CredentialStore", lambda: SimpleNamespace())
    monkeypatch.setattr(
        cli, "authenticate", lambda *a, **k: (SimpleNamespace(), "me@example.com")
    )
    monkeypatch.setattr(cli, "OllamaProvider", lambda *a, **k: SimpleNamespace())
    monkeypatch.setattr(cli, "Classifier", lambda *a, **k: SimpleNamespace())
    captured = {}

    def fake_scan(
        gmail_client,
        database,
        classifier,
        start,
        end,
        include_read=False,
        chunk_size="day",
        progress_callback=None,
        batch_size=100,
        **kwargs,
    ):
        captured["include_read"] = include_read
        captured["chunk_size"] = chunk_size
        captured["start"] = start
        return SimpleNamespace(
            as_dict=lambda: {
                "status": "completed",
                "messages": [],
                "categories": {},
                "counts": {},
                "historical_counts": {"deferred": False},
                "errors": [],
            }
        )

    monkeypatch.setattr(cli, "scan", fake_scan)
    # No CLI overrides: the [scan] config defaults apply.
    assert run_scan(config, as_json=True) == 0
    capsys.readouterr()
    assert captured["include_read"] is True
    assert captured["chunk_size"] == "week"
    now = datetime.now(UTC)
    assert captured["start"].date() == (now - timedelta(days=7)).date()


def test_run_scan_resumes_from_interrupted_state(tmp_path, capsys, monkeypatch):
    from datetime import UTC, datetime

    config = load_config(tmp_path / "home")
    database = Database(config.database_file)
    database.save_sync_state(
        status="failed",
        last_sync_date="2024-01-10T23:59:59.999999+00:00",
        total_processed=5,
    )
    database.close()
    config = replace(config, oauth_client_file=tmp_path / "client.json")
    monkeypatch.setattr(cli, "CredentialStore", lambda: SimpleNamespace())
    monkeypatch.setattr(
        cli, "authenticate", lambda *a, **k: (SimpleNamespace(), "me@example.com")
    )
    monkeypatch.setattr(cli, "OllamaProvider", lambda *a, **k: SimpleNamespace())
    monkeypatch.setattr(cli, "Classifier", lambda *a, **k: SimpleNamespace())
    captured = {}

    def fake_scan(
        gmail_client,
        database,
        classifier,
        start,
        end,
        include_read=False,
        chunk_size="day",
        progress_callback=None,
        batch_size=100,
        **kwargs,
    ):
        captured["start"] = start
        return SimpleNamespace(
            as_dict=lambda: {
                "status": "completed",
                "messages": [],
                "categories": {},
                "counts": {},
                "historical_counts": {"deferred": False},
                "errors": [],
            }
        )

    monkeypatch.setattr(cli, "scan", fake_scan)
    assert run_scan(config, as_json=True) == 0
    capsys.readouterr()
    # Resumes the day after the last processed chunk boundary.
    assert captured["start"] == datetime(2024, 1, 11, tzinfo=UTC)


def test_run_scan_does_not_resume_after_completed_scan(tmp_path, capsys, monkeypatch):
    config = load_config(tmp_path / "home")
    database = Database(config.database_file)
    database.save_sync_state(
        status="completed",
        last_sync_date="2024-01-10T23:59:59.999999+00:00",
        total_processed=5,
    )
    database.close()
    config = replace(config, oauth_client_file=tmp_path / "client.json")
    monkeypatch.setattr(cli, "CredentialStore", lambda: SimpleNamespace())
    monkeypatch.setattr(
        cli, "authenticate", lambda *a, **k: (SimpleNamespace(), "me@example.com")
    )
    monkeypatch.setattr(cli, "OllamaProvider", lambda *a, **k: SimpleNamespace())
    monkeypatch.setattr(cli, "Classifier", lambda *a, **k: SimpleNamespace())
    captured = {}

    def fake_scan(
        gmail_client,
        database,
        classifier,
        start,
        end,
        include_read=False,
        chunk_size="day",
        progress_callback=None,
        batch_size=100,
        **kwargs,
    ):
        captured["start"] = start
        return SimpleNamespace(
            as_dict=lambda: {
                "status": "completed",
                "messages": [],
                "categories": {},
                "counts": {},
                "historical_counts": {"deferred": False},
                "errors": [],
            }
        )

    monkeypatch.setattr(cli, "scan", fake_scan)
    assert run_scan(config, as_json=True) == 0
    capsys.readouterr()
    # A completed scan means today-only default (no resume).
    today_start = config.local_today_bounds()[0]
    assert captured["start"] == today_start


def test_scan_help_documents_historical_options(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["scan", "--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for flag in (
        "--start-date",
        "--end-date",
        "--last",
        "--include-read",
        "--chunk-size",
        "--verbose",
        "--debug",
    ):
        assert flag in out


def test_run_scan_json_excludes_progress(tmp_path, capsys, monkeypatch):
    """Progress goes to stderr so JSON output on stdout stays clean."""
    config = replace(
        load_config(tmp_path / "home"), oauth_client_file=tmp_path / "client.json"
    )
    monkeypatch.setattr(cli, "CredentialStore", lambda: SimpleNamespace())
    monkeypatch.setattr(
        cli, "authenticate", lambda *a, **k: (SimpleNamespace(), "me@example.com")
    )
    monkeypatch.setattr(cli, "OllamaProvider", lambda *a, **k: SimpleNamespace())
    monkeypatch.setattr(cli, "Classifier", lambda *a, **k: SimpleNamespace())

    def fake_scan(
        gmail_client,
        database,
        classifier,
        start,
        end,
        include_read=False,
        chunk_size="day",
        progress_callback=None,
        batch_size=100,
        **kwargs,
    ):
        if progress_callback:
            progress_callback(
                0,
                2,
                start,
                end,
                {"fetched": 1, "total_fetched": 1, "cached": 0},
            )
        return SimpleNamespace(
            as_dict=lambda: {
                "status": "completed",
                "messages": [],
                "categories": {},
                "counts": {},
                "historical_counts": {"deferred": False},
                "errors": [],
            }
        )

    monkeypatch.setattr(cli, "scan", fake_scan)
    assert run_scan(config, as_json=True, progress_level=2) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["status"] == "completed"
    assert "Scanning:" not in captured.out
    assert "Scanning:" in captured.err


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


def test_main_status_shows_sync_state(tmp_path, capsys):
    config = load_config(tmp_path / "home")
    database = Database(config.database_file)
    database.save_sync_state(
        status="completed",
        last_sync_date="2024-01-02T00:00:00+00:00",
        total_processed=5,
        chunk_size="day",
    )
    database.close()
    assert main(["--home", str(tmp_path / "home"), "status"]) == 0
    out = capsys.readouterr().out
    assert "Sync status: completed" in out
    assert "Last sync date: 2024-01-02T00:00:00+00:00" in out
    assert "Messages processed: 5" in out


def test_main_status_empty(tmp_path, capsys):
    assert main(["--home", str(tmp_path / "home"), "status"]) == 0
    assert "No scan has run yet" in capsys.readouterr().out


def test_main_status_reset_requires_confirmation(tmp_path, capsys, monkeypatch):
    config = load_config(tmp_path / "home")
    database = Database(config.database_file)
    database.save_sync_state(status="running")
    database.close()

    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert main(["--home", str(tmp_path / "home"), "status", "--reset"]) == 0
    assert "Reset cancelled" in capsys.readouterr().out
    database = Database(config.database_file)
    assert database.get_sync_state() is not None
    database.close()

    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert main(["--home", str(tmp_path / "home"), "status", "--reset"]) == 0
    database = Database(config.database_file)
    assert database.get_sync_state() is None
    database.close()


def test_main_scan_delegates(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cli, "run_scan", lambda config, as_json, progress_level=1, **kwargs: 3
    )
    assert main(["--home", str(tmp_path / "home"), "scan"]) == 3


def test_main_scan_debug_sets_progress_level(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        cli,
        "run_scan",
        lambda config, as_json, progress_level=1, **kwargs: calls.append(
            (as_json, progress_level)
        ),
    )
    main(["--home", str(tmp_path / "home"), "scan", "--debug"])
    assert calls == [(False, 3)]
    main(["--home", str(tmp_path / "home"), "scan", "--verbose"])
    assert calls == [(False, 3), (False, 2)]
