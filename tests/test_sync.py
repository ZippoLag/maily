from datetime import datetime, timezone
from pathlib import Path

from maily.classifier import Classifier
from maily.config import DEFAULT_CATEGORIES, load_config
from maily.db import Database
from maily.models import EmailMessage
from maily.sync import scan


class FakeGmail:
    def __init__(self, messages, error=None):
        self.messages = messages
        self.error = error

    def today_unread(self, start, end):
        if self.error:
            raise self.error
        return self.messages


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