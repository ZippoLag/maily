from datetime import datetime, timezone
from pathlib import Path

import pytest

from maily.classifier import Classifier
from maily.config import DEFAULT_CATEGORIES, Rule, load_config
from maily.db import Database
from maily.models import EmailMessage
from maily.sync import scan, split_date_range


class FakeGmail:
    def __init__(self, messages, error=None):
        self.messages = messages
        self.error = error
        self.queries = []

    def fetch_messages(self, start, end, include_read=False):
        self.queries.append((start, end, include_read))
        if self.error:
            raise self.error
        return self.messages

    def today_unread(self, start, end):
        return self.fetch_messages(start, end)


def test_scan_persists_and_reuses_classification(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    message = EmailMessage("m1", "t1", "", "person@example.com", "example.com", "Hello", "", datetime.now(timezone.utc), True, False)
    client = FakeGmail([message])
    classifier = Classifier(tuple(DEFAULT_CATEGORIES))
    first = scan(client, database, classifier, *config.local_today_bounds())
    second = scan(client, database, classifier, *config.local_today_bounds())
    assert first.status == "degraded"
    assert second.classifications["m1"].cached
    assert set(first.as_dict()["counts"]) == set(DEFAULT_CATEGORIES)
    database.close()


def test_split_date_range_day_chunks():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 3, 23, 59, 59, tzinfo=timezone.utc)
    chunks = split_date_range(start, end, "day")
    assert len(chunks) == 3
    assert chunks[0] == (datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc))


def test_split_date_range_week_and_month_and_year():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 3, 15, tzinfo=timezone.utc)
    assert len(split_date_range(start, end, "month")) == 3
    assert len(split_date_range(start, end, "year")) == 1
    week_chunks = split_date_range(start, end, "week")
    assert week_chunks[0][1].day == 7


def test_split_date_range_invalid_chunk_raises():
    with pytest.raises(ValueError):
        split_date_range(datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 2, tzinfo=timezone.utc), "hour")


def test_scan_historical_chunks_and_reports_progress(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    message = EmailMessage("m1", "t1", "", "person@example.com", "example.com", "Old email", "", datetime(2024, 1, 2, tzinfo=timezone.utc), True, False)
    client = FakeGmail([message])
    progress = []
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 3, tzinfo=timezone.utc)
    scan(client, database, Classifier(tuple(DEFAULT_CATEGORIES)), start, end, chunk_size="day", progress_callback=lambda *args: progress.append(args))
    assert len(client.queries) == 3  # one fetch per day chunk
    assert len(progress) == 3
    assert progress[0][0] == 0 and progress[0][1] == 3
    assert database.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1
    database.close()


def test_scan_include_read_passes_through(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    client = FakeGmail([])
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc)
    scan(client, database, Classifier(tuple(DEFAULT_CATEGORIES)), start, end, include_read=True)
    assert client.queries[0][2] is True
    database.close()


def test_scan_historical_caching_works(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    message = EmailMessage("m1", "t1", "", "person@example.com", "example.com", "Old email", "", datetime(2024, 1, 2, tzinfo=timezone.utc), True, False)
    client = FakeGmail([message])
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 3, tzinfo=timezone.utc)
    first = scan(client, database, Classifier(tuple(DEFAULT_CATEGORIES)), start, end)
    second = scan(client, database, Classifier(tuple(DEFAULT_CATEGORIES)), start, end)
    assert second.classifications["m1"].cached
    assert first.status in ("completed", "degraded")
    database.close()


def test_scan_applies_user_override_after_classification(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    message = EmailMessage("m1", "t1", "", "alerts@example.com", "example.com", "Your verification code", "", datetime.now(timezone.utc), True, False)
    client = FakeGmail([message])
    bounds = config.local_today_bounds()
    scan(client, database, Classifier(tuple(DEFAULT_CATEGORIES)), *bounds)
    database.set_user_override("m1", ["Personal"])
    second = scan(client, database, Classifier(tuple(DEFAULT_CATEGORIES)), *bounds)
    assert second.classifications["m1"].categories == ["Personal"]
    assert second.classifications["m1"].source == "override"
    database.close()


def test_scan_persists_original_and_override_separately(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    message = EmailMessage("m1", "t1", "", "alerts@example.com", "example.com", "Your verification code", "", datetime.now(timezone.utc), True, False)
    client = FakeGmail([message])
    bounds = config.local_today_bounds()
    scan(client, database, Classifier(tuple(DEFAULT_CATEGORIES)), *bounds)
    database.set_user_override("m1", ["Personal"])
    scan(client, database, Classifier(tuple(DEFAULT_CATEGORIES)), *bounds)
    stored_categories = [
        row[0] for row in database.connection.execute(
            "SELECT category FROM classifications WHERE message_id = 'm1'"
        )
    ]
    assert stored_categories == ["Action Required"]
    assert database.get_user_override("m1") == ["Personal"]
    database.close()


def test_rule_change_triggers_reclassification(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    message = EmailMessage("m1", "t1", "", "alerts@example.com", "example.com", "Your verification code", "", datetime.now(timezone.utc), True, False)
    client = FakeGmail([message])
    bounds = config.local_today_bounds()
    scan(client, database, Classifier(tuple(DEFAULT_CATEGORIES)), *bounds)
    changed = Classifier(tuple(DEFAULT_CATEGORIES), rules=(Rule("Action Required", ("payment due",)),))
    second = scan(client, database, changed, *bounds)
    assert not second.classifications["m1"].cached
    assert second.classifications["m1"].categories == ["Other"]
    database.close()


def test_failed_scan_keeps_last_completed_sync(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    message = EmailMessage("m1", "t1", "", "person@example.com", "example.com", "Hello", "", datetime.now(timezone.utc), True, False)
    bounds = config.local_today_bounds()
    scan(FakeGmail([message]), database, Classifier(tuple(DEFAULT_CATEGORIES)), *bounds)
    failed = scan(FakeGmail([], RuntimeError("offline")), database, Classifier(tuple(DEFAULT_CATEGORIES)), *bounds)
    assert failed.status == "failed"
    assert database.last_completed_sync() is not None
    assert database.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1
    database.close()