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
from .ollama import OllamaProvider
from .progress import ProgressReporter
from .secrets import CredentialStore, CredentialStoreError
from .sync import scan


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
        "scan", help="Scan today's unread Gmail messages"
    )
    scan_parser.add_argument("--json-format", action="store_true")
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


def run_scan(config, as_json: bool, progress_level: int = 1) -> int:
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
        start, end = config.local_today_bounds()
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
        return run_scan(config, args.json_format, progress_level)
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
