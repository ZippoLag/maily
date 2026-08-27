from __future__ import annotations

import base64
import email.utils
import json
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

from .models import EmailMessage

READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


class GmailClient(Protocol):
    def today_unread(self, start: datetime, end: datetime) -> list[EmailMessage]: ...

    def fetch_messages(
        self, start: datetime, end: datetime, include_read: bool = False
    ) -> list[EmailMessage]: ...


def parse_date(value: str) -> datetime:
    """Parse an ISO date or datetime string into a UTC datetime."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        parsed = datetime.strptime(value, "%Y-%m-%d")  # noqa: DTZ007 - converted to aware UTC below
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def parse_date_range(
    spec: str, now: datetime | None = None
) -> tuple[datetime, datetime]:
    """Parse a date range spec into (start, end) UTC datetimes.

    Supported forms:
    - ``last N days|weeks|months|years``
    - ``this month``
    - ``older-than Nd``
    - ``YYYY-MM-DD:YYYY-MM-DD`` explicit range
    """
    current = now or datetime.now(UTC)
    spec = spec.strip().lower()
    if ":" in spec:
        start_str, end_str = spec.split(":", 1)
        return parse_date(start_str), parse_date(end_str)
    match = re.fullmatch(
        r"last (\d+) (day|days|week|weeks|month|months|year|years)", spec
    )
    if match:
        count = int(match.group(1))
        unit = match.group(2).rstrip("s")
        if unit == "day":
            return current - timedelta(days=count), current
        if unit == "week":
            return current - timedelta(weeks=count), current
        if unit == "month":
            month = current.month - count
            year = current.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            return current.replace(
                year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0
            ), current
        if unit == "year":
            return current.replace(
                year=current.year - count,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ), current
    if spec == "this month":
        start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start, next_month - timedelta(microseconds=1)
    match = re.fullmatch(r"older-than (\d+)\s*(days?|weeks?|months?|years?)", spec)
    if match:
        count = int(match.group(1))
        unit = match.group(2).rstrip("s")
        if unit == "day":
            return _GMAIL_EPOCH, current - timedelta(days=count)
        if unit == "week":
            return _GMAIL_EPOCH, current - timedelta(weeks=count)
        if unit == "month":
            return _GMAIL_EPOCH, current - timedelta(days=30 * count)
        if unit == "year":
            return _GMAIL_EPOCH, current.replace(
                year=current.year - count,
                month=12,
                day=31,
                hour=23,
                minute=59,
                second=59,
                microsecond=999999,
            )
    raise ValueError(f"Unsupported date range: {spec}")


_GMAIL_EPOCH = datetime(2004, 1, 1, tzinfo=UTC)


def _build_query(start: datetime, end: datetime, include_read: bool, spam: bool) -> str:
    after = int(start.timestamp())
    before = int(end.timestamp()) + 1
    unread = "" if include_read else "is:unread "
    label = "label:spam" if spam else "-label:spam -label:trash"
    return f"{unread}after:{after} before:{before} {label}"


def _execute_with_retry(request, max_retries: int = 5, base_delay: float = 1.0):
    """Execute a Gmail API request with exponential backoff on rate limits.

    Retries 429 and quota/rate-limit 403 responses; other errors propagate
    immediately so quota exhaustion stops gracefully with a clear failure.
    """
    delay = base_delay
    attempt = 0
    while True:
        try:
            return request.execute()
        except Exception as exc:
            status = getattr(getattr(exc, "resp", None), "status", None)
            if status == 429 and attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                attempt += 1
                continue
            raise


def _header(headers: list[dict[str, str]], name: str) -> str:
    return next(
        (item["value"] for item in headers if item["name"].lower() == name.lower()), ""
    )


def _body(payload: dict[str, Any]) -> str:
    data = payload.get("body", {}).get("data")
    if data:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode(
            "utf-8", errors="replace"
        )
    return "\n".join(_body(part) for part in payload.get("parts", []))


def parse_message(raw: dict[str, Any], is_spam: bool) -> EmailMessage:
    headers = raw.get("payload", {}).get("headers", [])
    sender = _header(headers, "From")
    sender_name, sender_email = email.utils.parseaddr(sender)
    domain = sender_email.rsplit("@", 1)[-1].lower() if "@" in sender_email else ""
    received = datetime.fromtimestamp(int(raw.get("internalDate", "0")) / 1000, tz=UTC)
    return EmailMessage(
        id=raw["id"],
        thread_id=raw.get("threadId", raw["id"]),
        sender_name=sender_name,
        sender_email=sender_email,
        sender_domain=domain,
        subject=_header(headers, "Subject"),
        body=_body(raw.get("payload", {})),
        received_at=received,
        unread="UNREAD" in raw.get("labelIds", []),
        is_spam=is_spam,
    )


class GoogleGmailClient:
    def __init__(self, service):
        self.service = service

    def fetch_messages(
        self, start: datetime, end: datetime, include_read: bool = False
    ) -> list[EmailMessage]:
        messages: list[EmailMessage] = []
        for spam in (False, True):
            query = _build_query(start, end, include_read, spam)
            request = self.service.users().messages().list(userId="me", q=query)
            while request is not None:
                response = _execute_with_retry(request)
                for item in response.get("messages", []):
                    raw_request = (
                        self.service.users()
                        .messages()
                        .get(userId="me", id=item["id"], format="full")
                    )
                    raw = _execute_with_retry(raw_request)
                    messages.append(parse_message(raw, spam))
                token = response.get("nextPageToken")
                request = (
                    self.service.users()
                    .messages()
                    .list(userId="me", q=query, pageToken=token)
                    if token
                    else None
                )
        return messages

    def today_unread(self, start: datetime, end: datetime) -> list[EmailMessage]:
        return self.fetch_messages(start, end, include_read=False)


def validate_oauth_client_file(path: Path) -> None:
    if not path.exists():
        raise ValueError(f"OAuth client file does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"OAuth client file is not valid JSON: {path}") from exc
    if not isinstance(payload, dict) or not (
        payload.get("installed") or payload.get("web")
    ):
        raise ValueError(
            "OAuth client file must contain an installed or web client configuration"
        )


def build_authenticated_client(
    client_file: Path, token_json: str | None = None
) -> tuple[GoogleGmailClient, str, str]:
    validate_oauth_client_file(client_file)
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Install maily with the 'gmail' extra to connect to Gmail"
        ) from exc
    credentials = (
        Credentials.from_authorized_user_info(json.loads(token_json), [READONLY_SCOPE])
        if token_json
        else None
    )
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_file), [READONLY_SCOPE]
        )
        credentials = flow.run_local_server(port=0)
    service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    return GoogleGmailClient(service), profile["emailAddress"], credentials.to_json()
