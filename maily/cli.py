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
from .gmail import validate_oauth_client_file
from .ollama import OllamaProvider
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
    tui = subparsers.add_parser("tui", help="Browse the latest scan read-only")
    tui.add_argument("--json-format", action="store_true")
    fix = subparsers.add_parser(
        "fix", help="Check and repair configuration and database"
    )
    fix.add_argument(
        "--oauth-client-file", type=Path, help="Update the OAuth client file path"
    )
    return parser


def resolve_oauth_client_file(config) -> Path:
    """Resolve the OAuth client file with a robust fallback chain.

    1. If config has a path and the file exists, use it.
    2. If config has a path but file is missing, try auto-detecting in config.home.
    3. If config has no path, try auto-detecting in config.home.
    4. If nothing works, raise ValueError with clear guidance.
    """
    import glob as _glob

    configured = config.oauth_client_file
    home = config.home

    # Step 1: Try the configured path
    if configured is not None and configured.exists():
        return configured

    # Step 2 & 3: Auto-detect in config.home
    candidates = sorted(_glob.glob(str(home / "*apps.googleusercontent.com.json")))
    if candidates:
        return Path(candidates[0])

    # Step 4: Nothing found — build a clear error message
    if configured is not None and not configured.exists():
        raise ValueError(
            f"Configured oauth_client_file does not exist: {configured}\n"
            f"No *.apps.googleusercontent.com.json files found in {home}\n"
            "Run: maily init --oauth-client-file /path/to/client_secret.json"
        )
    raise ValueError(
        f"No *.apps.googleusercontent.com.json files found in {home}\n"
        "Place your OAuth client JSON in the config directory, or run:\n"
        "  maily init --oauth-client-file /path/to/client_secret.json"
    )


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


def run_scan(config, as_json: bool) -> int:
    database = Database(config.database_file)
    database.seed_categories(config.categories)
    try:
        credentials = CredentialStore()
        client_file = resolve_oauth_client_file(config)
        gmail_client, account = authenticate(client_file, database, credentials)
        provider = OllamaProvider(
            config.ollama_url, config.ollama_model, config.ollama_timeout_seconds
        )
        result = scan(
            gmail_client,
            database,
            Classifier(
                config.categories,
                provider,
                rules=config.rules,
                inference_enabled=config.inference_enabled,
            ),
            *config.local_today_bounds(),
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


def run_fix(config, oauth_client_file: Path | None = None) -> int:
    """Check and repair configuration and database state."""
    issues_fixed = []

    # 1. Update OAuth client file if provided
    if oauth_client_file:
        config_file = config.home / "config.toml"
        content = config_file.read_text(encoding="utf-8")
        client_path = (
            str(oauth_client_file.expanduser())
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )
        replacement = f'[gmail]\noauth_client_file = "{client_path}"'
        content = re.sub(
            r"\[gmail\]\s*oauth_client_file\s*=\s*[^\n]+", replacement, content
        )
        config_file.write_text(content, encoding="utf-8")
        issues_fixed.append(f"Updated oauth_client_file to {client_path}")

    # 2. Re-run database migration (safe, idempotent)
    db = Database(config.database_file)
    db.seed_categories(config.categories)
    db.close()
    issues_fixed.append("Database migration verified")

    # 3. Check OAuth file resolution
    try:
        client_file = resolve_oauth_client_file(config)
        issues_fixed.append(f"OAuth client file found: {client_file}")
    except ValueError as exc:
        print(f"WARNING: {exc}")

    # 4. Check logs directory
    logs_dir = config.home / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir(mode=0o700, exist_ok=True)
        issues_fixed.append("Created missing logs directory")

    if issues_fixed:
        print("Fixes applied:")
        for issue in issues_fixed:
            print(f"  ✓ {issue}")
    else:
        print("Configuration looks good. No fixes needed.")

    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.home)
    if args.command == "init":
        config_file = config.home / "config.toml"
        existing_config = config_file.exists()
        if args.oauth_client_file:
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
        if existing_config:
            print("Existing config found and preserved. New fields use defaults.")
        else:
            print(
                "Create a Google Cloud OAuth desktop client, download its JSON file, and configure gmail.oauth_client_file."
            )
        print(
            "Install optional integrations with: python -m pip install 'maily[gmail,secure,tui]'"
        )
        return 0
    if args.command == "scan":
        return run_scan(config, args.json_format)
    if args.command == "tui":
        from .tui import run_tui

        return run_tui(config, args.json_format)
    if args.command == "fix":
        return run_fix(config, args.oauth_client_file)
    return 2


if __name__ == "__main__":
    sys.exit(main())
