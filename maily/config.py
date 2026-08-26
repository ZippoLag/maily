from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


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
class MailyConfig:
    home: Path
    timezone: str
    oauth_client_file: Path | None
    ollama_url: str
    ollama_model: str
    ollama_timeout_seconds: float
    categories: tuple[str, ...]
    inference_enabled: bool = False

    @property
    def database_file(self) -> Path:
        return self.home / "maily.sqlite3"

    @property
    def logs_dir(self) -> Path:
        return self.home / "logs"

    def local_today_bounds(self, now: datetime | None = None) -> tuple[datetime, datetime]:
        current = now or datetime.now(ZoneInfo(self.timezone))
        local = current.astimezone(ZoneInfo(self.timezone))
        start = local.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start.replace(hour=23, minute=59, second=59, microsecond=999999)


def default_home() -> Path:
    return Path(os.environ.get("MAILY_HOME", Path.home() / ".maily")).expanduser()


def _write_default_config(path: Path) -> None:
    path.write_text(
        """timezone = \"{timezone}\"
ollama_url = \"http://127.0.0.1:11434\"
ollama_model = \"gemma4:e2b\"
ollama_timeout_seconds = 20
categories = [
{categories}]

[classification]
inference_enabled = false

[gmail]
oauth_client_file = \"\"
""".format(
            timezone=os.environ.get("TZ", "UTC"),
            categories="".join(f'  "{category}",\n' for category in DEFAULT_CATEGORIES),
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)


def load_config(home: Path | None = None) -> MailyConfig:
    state_home = (home or default_home()).expanduser()
    state_home.mkdir(mode=0o700, parents=True, exist_ok=True)
    state_home.chmod(0o700)
    (state_home / "logs").mkdir(mode=0o700, exist_ok=True)
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
    return MailyConfig(
        home=state_home,
        timezone=timezone,
        oauth_client_file=Path(client_file).expanduser() if client_file else None,
        ollama_url=raw.get("ollama_url", "http://127.0.0.1:11434").rstrip("/"),
        ollama_model=raw.get("ollama_model", "gemma4:e2b"),
        ollama_timeout_seconds=float(raw.get("ollama_timeout_seconds", 20)),
        categories=categories,
        inference_enabled=inference_enabled,
    )