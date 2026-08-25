import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from maily.gmail import parse_message, validate_oauth_client_file


def test_validate_oauth_client_file_rejects_invalid_input(tmp_path: Path):
    client_file = tmp_path / "client.json"
    client_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="installed or web"):
        validate_oauth_client_file(client_file)


def test_parse_message_extracts_sender_subject_body_and_spam_state():
    raw = {
        "id": "m1",
        "threadId": "t1",
        "internalDate": str(int(datetime(2026, 8, 25, tzinfo=timezone.utc).timestamp() * 1000)),
        "labelIds": ["UNREAD", "SPAM"],
        "payload": {
            "headers": [
                {"name": "From", "value": "Ada Lovelace <ada@example.com>"},
                {"name": "Subject", "value": "Hello"},
            ],
            "body": {"data": "SGVsbG8="},
        },
    }
    message = parse_message(raw, is_spam=True)
    assert message.sender_name == "Ada Lovelace"
    assert message.sender_domain == "example.com"
    assert message.body == "Hello"
    assert message.is_spam
    assert message.unread


def test_validate_oauth_client_file_accepts_installed_client(tmp_path: Path):
    client_file = tmp_path / "client.json"
    client_file.write_text(json.dumps({"installed": {"client_id": "id"}}), encoding="utf-8")
    validate_oauth_client_file(client_file)