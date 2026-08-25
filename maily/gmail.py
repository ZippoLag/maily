from __future__ import annotations

import base64
import email.utils
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .models import EmailMessage


READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


class GmailClient(Protocol):
    def today_unread(self, start: datetime, end: datetime) -> list[EmailMessage]: ...


def _header(headers: list[dict[str, str]], name: str) -> str:
    return next((item["value"] for item in headers if item["name"].lower() == name.lower()), "")


def _body(payload: dict[str, Any]) -> str:
    data = payload.get("body", {}).get("data")
    if data:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
    return "\n".join(_body(part) for part in payload.get("parts", []))


def parse_message(raw: dict[str, Any], is_spam: bool) -> EmailMessage:
    headers = raw.get("payload", {}).get("headers", [])
    sender = _header(headers, "From")
    sender_name, sender_email = email.utils.parseaddr(sender)
    domain = sender_email.rsplit("@", 1)[-1].lower() if "@" in sender_email else ""
    received = datetime.fromtimestamp(int(raw.get("internalDate", "0")) / 1000, tz=timezone.utc)
    return EmailMessage(
        id=raw["id"], thread_id=raw.get("threadId", raw["id"]), sender_name=sender_name,
        sender_email=sender_email, sender_domain=domain, subject=_header(headers, "Subject"),
        body=_body(raw.get("payload", {})), received_at=received,
        unread="UNREAD" in raw.get("labelIds", []), is_spam=is_spam,
    )


class GoogleGmailClient:
    def __init__(self, service):
        self.service = service

    def today_unread(self, start: datetime, end: datetime) -> list[EmailMessage]:
        after = int(start.timestamp())
        before = int(end.timestamp()) + 1
        messages: list[EmailMessage] = []
        for query, spam in ((f"is:unread after:{after} before:{before} -label:spam -label:trash", False),
                            (f"is:unread after:{after} before:{before} label:spam", True)):
            request = self.service.users().messages().list(userId="me", q=query)
            while request is not None:
                response = request.execute()
                for item in response.get("messages", []):
                    raw = self.service.users().messages().get(userId="me", id=item["id"], format="full").execute()
                    messages.append(parse_message(raw, spam))
                token = response.get("nextPageToken")
                request = self.service.users().messages().list(userId="me", q=query, pageToken=token) if token else None
        return messages


def validate_oauth_client_file(path: Path) -> None:
    if not path.exists():
        raise ValueError(f"OAuth client file does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"OAuth client file is not valid JSON: {path}") from exc
    if not isinstance(payload, dict) or not (payload.get("installed") or payload.get("web")):
        raise ValueError("OAuth client file must contain an installed or web client configuration")


def build_authenticated_client(client_file: Path, token_json: str | None = None) -> tuple[GoogleGmailClient, str, str]:
    validate_oauth_client_file(client_file)
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Install maily with the 'gmail' extra to connect to Gmail") from exc
    credentials = Credentials.from_authorized_user_info(json.loads(token_json), [READONLY_SCOPE]) if token_json else None
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_file), [READONLY_SCOPE])
        credentials = flow.run_local_server(port=0)
    service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    return GoogleGmailClient(service), profile["emailAddress"], credentials.to_json()