from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SCAN_CHUNK_SIZES = ("day", "week", "month", "year")


DEFAULT_CATEGORIES = [
    "Action Required",
    "Personal",
    "Work",
    "Work proposals",
    "Job search",
    "Newsletters - technical",
    "Newsletters - other",
    "Other",
]


@dataclass(frozen=True)
class Rule:
    """A classification rule with category, patterns, and fields to match against."""

    category: str
    patterns: tuple[str, ...]
    fields: tuple[str, ...] = ("subject", "body", "sender_email")

    def matches(self, message: Any) -> tuple[str, ...]:
        """Return the rule's patterns that matched the message, empty tuple if none."""
        values = [getattr(message, field, "") for field in self.fields]
        haystack = "\n".join(values).lower()
        return tuple(
            pattern
            for pattern in self.patterns
            if re.search(pattern, haystack, re.IGNORECASE)
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize rule to dictionary."""
        return {
            "category": self.category,
            "patterns": list(self.patterns),
            "fields": list(self.fields),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        """Deserialize rule from dictionary."""
        return cls(
            category=data["category"],
            patterns=tuple(data["patterns"]),
            fields=tuple(data.get("fields", ["subject", "body", "sender_email"])),
        )


def parse_rule(rule_dict: dict[str, Any]) -> Rule:
    """Parse a single rule from TOML dictionary."""
    category = rule_dict.get("category")
    if not category:
        raise ValueError(f"Rule missing 'category': {rule_dict}")

    patterns = rule_dict.get("patterns", [])
    if not patterns:
        raise ValueError(f"Rule '{category}' has no patterns")

    for pattern in patterns:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(
                f"Invalid regex pattern in rule '{category}': {pattern} - {exc}"
            ) from exc

    fields = rule_dict.get("fields", ["subject", "body", "sender_email"])

    return Rule(category=category, patterns=tuple(patterns), fields=tuple(fields))


def parse_rules(rules_config: list[dict[str, Any]] | None) -> tuple[Rule, ...]:
    """Parse classification rules from TOML configuration."""
    if not rules_config:
        return ()
    return tuple(parse_rule(rule_dict) for rule_dict in rules_config)


DEFAULT_RULES = (
    Rule(
        "Action Required",
        (
            r"verify",
            r"verification code",
            r"expires?",
            r"due date",
            r"payment required",
        ),
    ),
    Rule("Job search", (r"job alert", r"career", r"vacancy", r"hiring", r"recruit")),
    Rule(
        "Newsletters - technical",
        (r"unsubscribe", r"developer", r"software", r"release notes"),
    ),
)


@dataclass(frozen=True)
class MailyConfig:
    home: Path
    timezone: str
    oauth_client_file: Path | None
    ollama_url: str
    ollama_model: str
    ollama_timeout_seconds: float
    categories: tuple[str, ...]
    inference_enabled: bool = False
    rules: tuple[Rule, ...] = DEFAULT_RULES
    scan_date_range: str | None = None
    scan_include_read: bool = False
    scan_chunk_size: str = "day"

    @property
    def database_file(self) -> Path:
        return self.home / "maily.sqlite3"

    @property
    def logs_dir(self) -> Path:
        return self.home / "logs"

    def local_today_bounds(
        self, now: datetime | None = None
    ) -> tuple[datetime, datetime]:
        current = now or datetime.now(ZoneInfo(self.timezone))
        local = current.astimezone(ZoneInfo(self.timezone))
        start = local.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start.replace(hour=23, minute=59, second=59, microsecond=999999)


def default_home() -> Path:
    return Path(os.environ.get("MAILY_HOME", Path.home() / ".maily")).expanduser()


def validate_scan_config(
    date_range: str | None, include_read: bool, chunk_size: str
) -> None:
    """Validate the [scan] section, raising ValueError on invalid values."""
    if date_range is not None:
        try:
            from .gmail import parse_date_range

            parse_date_range(date_range)
        except ValueError as exc:
            raise ValueError(
                f"Invalid scan.date_range: {date_range!r} ({exc})"
            ) from exc
    if chunk_size not in SCAN_CHUNK_SIZES:
        raise ValueError(
            "Invalid scan.chunk_size: "
            f"{chunk_size!r} (expected one of {', '.join(SCAN_CHUNK_SIZES)})"
        )


def _write_default_config(path: Path) -> None:
    categories_str = "".join(f'  "{category}",\n' for category in DEFAULT_CATEGORIES)
    config_content = f"""timezone = "{os.environ.get("TZ", "UTC")}"
ollama_url = "http://127.0.0.1:11434"
ollama_model = "gemma4:e2b"
ollama_timeout_seconds = 20
categories = [
{categories_str}]

[classification]
inference_enabled = false

# User-defined static analysis rules for classification
# Rules are applied before inference and allow deterministic categorization
# Each rule has: category, patterns (regex), fields (optional, defaults to ["subject", "body", "sender_email"])
# Example:
# [[classification.rules]]
# category = "Work"
# patterns = [
#   "meeting invitation",
#   "project update",
#   "status report"
# ]
# fields = ["subject", "body"]

# [[classification.rules]]
# category = "Personal"
# patterns = [
#   "family",
#   "friend",
#   "weekend plans"
# ]

[scan]
# Optional defaults for historical scans; CLI flags override these.
# date_range = "last 30 days"   # "last 7 days", "this month", "2024-01-01:2024-01-31"
# include_read = false          # set true to include already-read emails
# chunk_size = "day"            # day | week | month | year

[gmail]
oauth_client_file = ""
"""
    path.write_text(config_content, encoding="utf-8")
    path.chmod(0o600)


def load_config(home: Path | None = None) -> MailyConfig:
    state_home = (home or default_home()).expanduser()
    state_home.mkdir(mode=0o700, parents=True, exist_ok=True)
    state_home.chmod(0o700)
    config_file = state_home / "config.toml"
    if not config_file.exists():
        _write_default_config(config_file)
    with config_file.open("rb") as stream:
        raw = tomllib.load(stream)
    gmail = raw.get("gmail", {})
    client_file = gmail.get("oauth_client_file", "")
    timezone = raw.get("timezone", "UTC")
    try:
        ZoneInfo(timezone)
    except Exception as exc:
        raise ValueError(f"Invalid configured timezone: {timezone}") from exc
    categories = tuple(dict.fromkeys([*DEFAULT_CATEGORIES, *raw.get("categories", [])]))
    classification = raw.get("classification", {})
    inference_enabled = classification.get("inference_enabled", False)

    user_rules = parse_rules(classification.get("rules"))

    scan = raw.get("scan", {})
    scan_date_range = scan.get("date_range")
    scan_include_read = scan.get("include_read", False)
    scan_chunk_size = scan.get("chunk_size", "day")
    validate_scan_config(scan_date_range, scan_include_read, scan_chunk_size)

    return MailyConfig(
        home=state_home,
        timezone=timezone,
        oauth_client_file=Path(client_file).expanduser() if client_file else None,
        ollama_url=raw.get("ollama_url", "http://127.0.0.1:11434").rstrip("/"),
        ollama_model=raw.get("ollama_model", "gemma4:e2b"),
        ollama_timeout_seconds=float(raw.get("ollama_timeout_seconds", 20)),
        categories=categories,
        inference_enabled=inference_enabled,
        rules=(*DEFAULT_RULES, *user_rules),
        scan_date_range=scan_date_range,
        scan_include_read=scan_include_read,
        scan_chunk_size=scan_chunk_size,
    )
