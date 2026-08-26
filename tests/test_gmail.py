import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from maily.gmail import (
    GoogleGmailClient,
    _build_query,
    _execute_with_retry,
    parse_date,
    parse_date_range,
    parse_message,
    validate_oauth_client_file,
)


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


def test_parse_date_iso_format():
    assert parse_date("2024-01-01") == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_parse_date_iso_datetime_format():
    assert parse_date("2024-01-01T12:00:00") == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_date_range_last_7_days():
    now = datetime(2024, 1, 31, 12, 0, tzinfo=timezone.utc)
    start, end = parse_date_range("last 7 days", now=now)
    assert start == datetime(2024, 1, 24, 12, 0, tzinfo=timezone.utc)
    assert end == now


def test_parse_date_range_this_month():
    now = datetime(2024, 1, 31, 12, 0, tzinfo=timezone.utc)
    start, end = parse_date_range("this month", now=now)
    assert start == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert end.day == 31


def test_parse_date_range_explicit_range():
    start, end = parse_date_range("2024-01-01:2024-01-31")
    assert start == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert end == datetime(2024, 1, 31, tzinfo=timezone.utc)


def test_parse_date_range_invalid_raises():
    with pytest.raises(ValueError):
        parse_date_range("not a range")


def test_build_query_unread_excludes_spam_trash():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc)
    query = _build_query(start, end, include_read=False, spam=False)
    assert query.startswith("is:unread ")
    assert "after:1704067200" in query
    assert "-label:spam -label:trash" in query


def test_build_query_include_read_omits_unread_filter():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc)
    query = _build_query(start, end, include_read=True, spam=False)
    assert not query.startswith("is:unread ")


class FakeRequest:
    def __init__(self, responses):
        self.responses = list(responses)
        self.executions = 0

    def execute(self):
        if self.executions < len(self.responses):
            response = self.responses[self.executions]
            self.executions += 1
            if isinstance(response, Exception):
                raise response
            return response
        raise AssertionError("no more responses")


class RateLimitError(Exception):
    class Resp:
        status = 429

    resp = Resp()


class QuotaError(Exception):
    class Resp:
        status = 403

    resp = Resp()


def test_execute_with_retry_backs_off_on_rate_limit():
    request = FakeRequest([RateLimitError(), RateLimitError(), {"messages": []}])
    assert _execute_with_retry(request, max_retries=5, base_delay=0) == {"messages": []}
    assert request.executions == 3


def test_execute_with_retry_stops_after_max_retries():
    request = FakeRequest([RateLimitError(), RateLimitError(), RateLimitError(), RateLimitError()])
    with pytest.raises(RateLimitError):
        _execute_with_retry(request, max_retries=2, base_delay=0)


def test_execute_with_retry_reports_quota_error():
    request = FakeRequest([QuotaError()])
    with pytest.raises(QuotaError):
        _execute_with_retry(request, max_retries=5, base_delay=0)


def test_fetch_messages_passes_include_read_to_query():
    class FakeService:
        def __init__(self):
            self.queries = []

        def users(self):
            return self

        def messages(self):
            return self

        def list(self, **kwargs):
            self.queries.append(kwargs)
            return FakeRequest([{"messages": []}])

        def get(self, **kwargs):
            raise AssertionError("no raw message fetches expected")

    service = FakeService()
    client = GoogleGmailClient(service)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc)
    client.fetch_messages(start, end, include_read=True)
    assert not any("is:unread" in kwargs["q"] for kwargs in service.queries)
    assert len(service.queries) == 2  # non-spam + spam