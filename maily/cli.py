from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from . import __version__
from .auth import authenticate
from .classifier import Classifier
from .config import load_config
from .db import Database
from .gmail import parse_date, parse_date_range
from .ollama import OllamaProvider
from .progress import ProgressReporter
from .secrets import CredentialStore, CredentialStoreError
from .sync import CHUNK_SIZES, scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="maily", description="Local Gmail triage")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--home", type=Path, help="Override the ~/.maily state directory"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser(
        "init", help="Create local state and show setup instructions"
    )
    init.add_argument("--oauth-client-file", type=Path)
    scan_parser = subparsers.add_parser(
        "scan", help="Scan Gmail messages, optionally over a historical date range"
    )
    scan_parser.add_argument("--json-format", action="store_true")
    scan_parser.add_argument("--start-date", help="Scan from this date (YYYY-MM-DD)")
    scan_parser.add_argument("--end-date", help="Scan up to this date (YYYY-MM-DD)")
    scan_parser.add_argument(
        "--last",
        help="Scan the last N days/weeks/months/years (e.g. --last 7days)",
    )
    scan_parser.add_argument(
        "--include-read",
        action="store_true",
        default=None,
        help="Include already-read emails in the scan (defaults to the [scan] config)",
    )
    scan_parser.add_argument(
        "--chunk-size",
        choices=CHUNK_SIZES,
        help="Date chunk size for progress reporting (day/week/month/year)",
    )
    scan_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show processing rate and ETA in progress output",
    )
    scan_parser.add_argument(
        "--debug",
        action="store_true",
        help="Show per-chunk debug details in progress output",
    )
    tui = subparsers.add_parser("tui", help="Browse the latest scan read-only")
    tui.add_argument("--json-format", action="store_true")
    status = subparsers.add_parser("status", help="Show scan progress and sync state")
    status.add_argument(
        "--reset", action="store_true", help="Reset sync state (asks for confirmation)"
    )
    return parser


def render_human(result: dict) -> str:
    lines = [
        f"Scan: {result['status']}",
        f"Messages synchronized: {len(result['messages'])}",
    ]
    for category in sorted(result["counts"]):
        count = result["counts"][category]
        lines.append(f"{category}: {count}")
        if category == "Action Required" and count > 0:
            for message in result.get("categories", {}).get(category, []):
                subject = message.get("subject") or "(no subject)"
                sender_email = message.get("sender_email", "")
                lines.append(f"  - {subject} ({sender_email})")
    if result["historical_counts"]["deferred"]:
        lines.append("Historical unread and read counts: deferred")
    for error in result["errors"]:
        lines.append(f"Error: {error}")
    return "\n".join(lines)


def _normalize_last(value: str) -> str:
    """Turn ``7days``/``7 days`` into the ``last N unit`` spec parse_date_range accepts."""
    match = re.fullmatch(
        r"(\d+)\s*(days?|weeks?|months?|years?)", value.strip().lower()
    )
    if match:
        return f"last {match.group(1)} {match.group(2)}"
    return f"last {value.strip().lower()}"


def _scan_window(config, start_date, end_date, last):
    """Resolve the scan window from CLI overrides or the [scan] config."""
    if not any((start_date, end_date, last)) and config.scan_date_range:
        return parse_date_range(config.scan_date_range)
    return resolve_scan_bounds(config, start_date, end_date, last)


def resolve_scan_bounds(config, start_date, end_date, last):
    """Resolve the scan window from CLI overrides, defaulting to today.

    Priority: ``--last`` relative spec, then explicit ``--start-date``/``--end-date``
    (each defaulting to today when omitted), then the config's today-only bounds.
    """
    today_start, today_end = config.local_today_bounds()
    if last:
        return parse_date_range(_normalize_last(last))
    if start_date or end_date:
        start = parse_date(start_date) if start_date else today_start
        end = parse_date(end_date) if end_date else today_end
        return start, end
    return today_start, today_end


def run_status(config, reset: bool = False) -> int:
    database = Database(config.database_file)
    try:
        state = database.get_sync_state()
        if reset:
            if state is None:
                print("No sync state to reset.")
                return 0
            answer = input("Reset sync state? This clears scan progress. [y/N] ")
            if answer.strip().lower() != "y":
                print("Reset cancelled.")
                return 0
            database.reset_sync_state()
            print("Sync state reset.")
            return 0
        if state is None:
            print("No scan has run yet.")
            return 0
        print(f"Sync status: {state['status']}")
        if state["last_sync_date"]:
            print(f"Last sync date: {state['last_sync_date']}")
        print(f"Messages processed: {state['total_processed']}")
        if state["started_at"]:
            print(f"Started: {state['started_at']}")
        if state["completed_at"]:
            print(f"Completed: {state['completed_at']}")
        print(f"Chunk size: {state['chunk_size']}")
        return 0
    finally:
        database.close()


def run_scan(
    config,
    as_json: bool,
    progress_level: int = 1,
    start_date=None,
    end_date=None,
    last=None,
    include_read: bool | None = None,
    chunk_size: str | None = None,
) -> int:
    database = Database(config.database_file)
    database.seed_categories(config.categories)
    reporter = ProgressReporter(level=progress_level)
    try:
        credentials = CredentialStore()
        client_file = config.oauth_client_file
        if client_file is None:
            raise ValueError(
                "Configure gmail.oauth_client_file in ~/.maily/config.toml or run maily init --oauth-client-file PATH"
            )
        gmail_client, account = authenticate(client_file, database, credentials)
        provider = OllamaProvider(
            config.ollama_url, config.ollama_model, config.ollama_timeout_seconds
        )
        start, end = _scan_window(config, start_date, end_date, last)
        effective_include_read = (
            config.scan_include_read if include_read is None else include_read
        )
        effective_chunk_size = chunk_size or config.scan_chunk_size
        result = scan(
            gmail_client,
            database,
            Classifier(
                config.categories,
                provider,
                rules=config.rules,
                inference_enabled=config.inference_enabled,
            ),
            start,
            end,
            include_read=effective_include_read,
            chunk_size=effective_chunk_size,
            progress_callback=reporter.update,
        )
        payload = result.as_dict()
        payload["account"] = account
    except (CredentialStoreError, ValueError, RuntimeError) as exc:
        payload = {
            "status": "failed",
            "messages": [],
            "categories": {},
            "counts": {},
            "historical_counts": {"deferred": True},
            "errors": [str(exc)],
        }
        result = None
    finally:
        database.close()
    print(json.dumps(payload, indent=2) if as_json else render_human(payload))
    return 0 if payload["status"] in ("completed", "degraded") else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.home)
    if args.command == "init":
        if args.oauth_client_file:
            config_file = config.home / "config.toml"
            content = config_file.read_text(encoding="utf-8")
            client_path = (
                str(args.oauth_client_file.expanduser())
                .replace("\\", "\\\\")
                .replace('"', '\\"')
            )
            replacement = f'[gmail]\noauth_client_file = "{client_path}"'
            content = re.sub(
                r"\[gmail\]\s*oauth_client_file\s*=\s*[^\n]+", replacement, content
            )
            config_file.write_text(content, encoding="utf-8")
        print(f"State initialized at {config.home}")
        print(
            "Create a Google Cloud OAuth desktop client, download its JSON file, and configure gmail.oauth_client_file."
        )
        print(
            "Install optional integrations with: python -m pip install 'maily[gmail,secure,tui]'"
        )
        return 0
    if args.command == "scan":
        progress_level = 3 if args.debug else (2 if args.verbose else 1)
        return run_scan(
            config,
            args.json_format,
            progress_level,
            start_date=args.start_date,
            end_date=args.end_date,
            last=args.last,
            include_read=args.include_read,
            chunk_size=args.chunk_size,
        )
    if args.command == "status":
        return run_status(config, args.reset)
    if args.command == "tui":
        try:
            from .tui import run_tui

            return run_tui(config, args.json_format)
        except RuntimeError as exc:
            print(f"maily: {exc}", file=sys.stderr)
            return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
