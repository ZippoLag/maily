"""Tests for corner-cases-large-scale: long-running scans, resilience, memory."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from maily.classifier import Classifier
from maily.config import DEFAULT_CATEGORIES, load_config
from maily.db import Database
from maily.gmail import _error_reason, _is_quota_reason
from maily.models import EmailMessage
from maily.progress import JsonlLogger, memory_usage_mb, warn_on_memory
from maily.suggestions import generate_suggestions, sample_for_analysis
from maily.sync import ScanLock, classify_error, scan
from maily.tui import BrowseApp


def _message(mid: str, received: datetime, subject: str = "Hi") -> EmailMessage:
    return EmailMessage(
        mid,
        f"t-{mid}",
        "A",
        f"{mid}@example.com",
        "example.com",
        subject,
        "body",
        received,
        True,
        False,
    )


class FakeGmail:
    """Serves a fixed list; raises *error* when given instead."""

    def __init__(self, messages, error: Exception | None = None):
        self.messages = messages
        self.error = error

    def fetch_messages(self, start, end, include_read=False):
        if self.error is not None:
            raise self.error
        return self.messages


# ── Config (tasks 12.1-12.3) ────────────────────────────────────────────


def test_config_parses_long_running_and_performance(tmp_path):
    home = tmp_path / "home"
    home.mkdir(parents=True)
    (home / "config.toml").write_text(
        'timezone = "UTC"\n'
        "[scan]\nlong_running = true\nbatch_size = 25\ncheckpoint_emails = 10\n"
        "max_retries = 3\n"
        "[performance]\nmemory_limit_mb = 512\nbody_cache_size = 42\n"
        "[suggestions]\nconfidence_threshold = 0.5\n"
        '[gmail]\noauth_client_file = ""\n'
    )
    config = load_config(home)
    assert config.scan_long_running is True
    assert config.scan_batch_size == 25
    assert config.scan_checkpoint_emails == 10
    assert config.scan_max_retries == 3
    assert config.performance_memory_limit_mb == 512
    assert config.performance_body_cache_size == 42
    assert config.suggestions_confidence_threshold == 0.5


def test_config_rejects_bad_batch_size(tmp_path):
    home = tmp_path / "home"
    home.mkdir(parents=True)
    (home / "config.toml").write_text(
        'timezone = "UTC"\n[scan]\nbatch_size = 0\n[gmail]\noauth_client_file = ""\n'
    )
    import pytest

    with pytest.raises(ValueError):
        load_config(home)


# ── Error classification (tasks 5.1) ────────────────────────────────────


def test_classify_error_categories():
    assert classify_error(TimeoutError("timed out")) == "network"
    assert classify_error(RuntimeError("quota exceeded")) == "quota"
    assert classify_error(RuntimeError("userRateLimitExceeded")) == "quota"
    assert classify_error(RuntimeError("connection reset")) == "network"
    assert classify_error(RuntimeError("weird thing")) == "unknown"


def test_quota_reason_detection():
    assert _is_quota_reason("userRateLimitExceeded")
    assert _is_quota_reason("quotaExceeded")
    assert not _is_quota_reason("invalidArgument")
    assert _error_reason(RuntimeError("boom")) != ""


# ── Scan lock (tasks 1.4) ───────────────────────────────────────────────


def test_scan_lock_prevents_concurrent(tmp_path):
    lock_path = tmp_path / "scan.lock"
    import pytest

    with ScanLock(lock_path, enabled=True):
        assert lock_path.exists()
        with (
            pytest.raises(RuntimeError, match="Another scan"),
            ScanLock(lock_path, enabled=True),
        ):
            pass
    assert not lock_path.exists()


def test_scan_lock_disabled_when_not_long_running(tmp_path):
    lock_path = tmp_path / "scan.lock"
    with ScanLock(lock_path, enabled=False):
        assert not lock_path.exists()


# ── Long-running scan completes (tasks 1.1-1.5, 13.1) ───────────────────


def test_long_running_scan_completes(tmp_path):
    config = load_config(tmp_path / "home")
    db = Database(config.database_file)
    db.seed_categories(tuple(DEFAULT_CATEGORIES))
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2024, 1, 2, 23, 59, 59, tzinfo=UTC)
    result = scan(
        FakeGmail([_message("m1", start)]),
        db,
        Classifier(tuple(DEFAULT_CATEGORIES)),
        start,
        end,
        chunk_size="day",
        long_running=True,
        checkpoint_emails=1,
    )
    assert result.status in ("completed", "degraded")
    # The long-running lock file is cleaned up.
    assert not Path(db.path).with_name("scan.lock").exists()
    db.close()


# ── Checkpoint + resume state (tasks 2.3-2.5, 13.2) ─────────────────────


def test_checkpoint_saves_sync_state(tmp_path):
    config = load_config(tmp_path / "home")
    db = Database(config.database_file)
    db.seed_categories(tuple(DEFAULT_CATEGORIES))
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2024, 1, 2, 23, 59, 59, tzinfo=UTC)
    scan(
        FakeGmail([_message("m1", start), _message("m2", start)]),
        db,
        Classifier(tuple(DEFAULT_CATEGORIES)),
        start,
        end,
        chunk_size="day",
        checkpoint_emails=1,
    )
    state = db.get_sync_state()
    assert state is not None
    assert state["total_processed"] >= 1
    assert state["last_sync_date"] is not None
    db.close()


# ── Error resilience (tasks 5.2-5.3, 5.6, 13.3, 13.9) ───────────────────


def test_scan_continues_after_chunk_failure(tmp_path):
    config = load_config(tmp_path / "home")
    db = Database(config.database_file)
    db.seed_categories(tuple(DEFAULT_CATEGORIES))
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2024, 1, 3, 23, 59, 59, tzinfo=UTC)

    class Flaky:
        def __init__(self):
            self.calls = 0

        def fetch_messages(self, start, end, include_read=False):
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError("api outage")
            return [_message(f"m{self.calls}", start)]

    result = scan(
        Flaky(),
        db,
        Classifier(tuple(DEFAULT_CATEGORIES)),
        start,
        end,
        chunk_size="day",
    )
    assert result.status == "degraded"  # partial success
    assert any("api outage" in e for e in result.errors)
    assert len(result.messages) >= 2
    db.close()


def test_all_chunks_failing_is_failed(tmp_path):
    config = load_config(tmp_path / "home")
    db = Database(config.database_file)
    db.seed_categories(tuple(DEFAULT_CATEGORIES))
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2024, 1, 1, 23, 59, 59, tzinfo=UTC)
    result = scan(
        FakeGmail([], RuntimeError("offline")),
        db,
        Classifier(tuple(DEFAULT_CATEGORIES)),
        start,
        end,
        chunk_size="day",
    )
    assert result.status == "failed"
    assert db.get_sync_state()["status"] == "failed"
    db.close()


# ── JSON Lines logging + error log (tasks 2.6, 4.5, 5.7) ────────────────


def test_jsonl_logger_writes_entries(tmp_path):
    path = tmp_path / "scan_progress.jsonl"
    logger = JsonlLogger(path)
    logger.log(event="chunk_done", total_fetched=10)
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 1
    assert '"total_fetched": 10' in lines[0]


def test_error_log_written_on_degraded_scan(tmp_path):
    config = load_config(tmp_path / "home")
    db = Database(config.database_file)
    db.seed_categories(tuple(DEFAULT_CATEGORIES))
    logs_dir = tmp_path / "logs"
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2024, 1, 1, 23, 59, 59, tzinfo=UTC)
    result = scan(
        FakeGmail([], RuntimeError("offline")),
        db,
        Classifier(tuple(DEFAULT_CATEGORIES)),
        start,
        end,
        chunk_size="day",
        logs_dir=logs_dir,
    )
    assert result.status == "failed"
    assert (logs_dir / "scan_errors.log").exists()
    db.close()


# ── Memory (tasks 7.1-7.7, 13.5) ────────────────────────────────────────


def test_warn_on_memory_limit():
    assert warn_on_memory(None) is None
    assert warn_on_memory(0) is None
    # With a tiny limit the current RSS (usually > 0 MB) crosses 80%.
    warning = warn_on_memory(1)
    if memory_usage_mb() > 0:
        assert warning is not None
        assert "Memory warning" in warning


def test_body_cache_lru_evicts(tmp_path):
    config = load_config(tmp_path / "home")
    db = Database(config.database_file, body_cache_size=2)
    db.seed_categories(("Work",))
    db.connection.execute("INSERT INTO threads(id) VALUES ('t1')")
    for i in range(3):
        db.connection.execute(
            "INSERT INTO messages(id, thread_id, subject, body, received_at, "
            "unread, is_spam, synced_at) VALUES (?, 't1', 's', ?, "
            "'2026-08-27T10:00:00', 1, 0, '2026-08-27T10:00:00')",
            (f"m{i}", f"body{i}"),
        )
    db.connection.commit()
    assert db.get_message_body("m0") == "body0"
    assert db.get_message_body("m1") == "body1"
    assert db.get_message_body("m2") == "body2"  # evicts m0
    assert len(db._body_cache) == 2
    assert "m0" not in db._body_cache
    db.close()


# ── Sampling (task 8.6) ─────────────────────────────────────────────────


def test_sample_for_analysis_bounds_large_sets():
    emails = [{"id": f"m{i}"} for i in range(1000)]
    sampled = sample_for_analysis(emails, limit=50)
    assert len(sampled) == 50
    assert all(e["id"] in {f"m{i}" for i in range(1000)} for e in sampled)


# ── Suggestion confidence threshold (tasks 8.3, 12.3) ───────────────────


def test_confidence_threshold_filters_suggestions():
    emails = [
        {
            "id": f"m{i}",
            "sender_name": "News",
            "sender_domain": "news.com",
            "subject": "unsubscribe",
            "labels": ["Newsletter"],
            "category": "Newsletters - other",
        }
        for i in range(3)
    ]
    unfiltered = generate_suggestions(emails)
    assert unfiltered
    filtered = generate_suggestions(emails, confidence_threshold=0.9)
    assert all(s.confidence >= 0.9 for s in filtered)


# ── Mutation intents (tasks 10.1-10.5, 13.8) ────────────────────────────


def test_mutation_intent_crud(tmp_path):
    config = load_config(tmp_path / "home")
    db = Database(config.database_file)
    db.seed_categories(("Work",))
    intent_id = db.save_mutation_intent(
        "archive", ["m1", "m2"], "domain: news.com", "archive 2 emails"
    )
    intents = db.list_mutation_intents()
    assert len(intents) == 1
    assert intents[0]["action"] == "archive"
    assert intents[0]["message_ids"] == ["m1", "m2"]
    db.clear_mutation_intents([intent_id])
    assert db.list_mutation_intents() == []
    db.close()


# ── TUI: batch suggestions + intents + undo (tasks 9.x, 10.4, 13.8) ─────


def _seed_one(config):
    db = Database(config.database_file)
    db.seed_categories(tuple(config.categories))
    db.connection.execute("INSERT INTO threads(id) VALUES ('t1')")
    db.connection.execute(
        "INSERT INTO messages(id, thread_id, sender_name, sender_email, "
        "subject, body, received_at, unread, is_spam, labels, synced_at) "
        "VALUES ('m1', 't1', 'News', 'news@example.com', 'unsubscribe', 'b', "
        "'2026-08-27T10:00:00', 1, 0, '[\"Newsletter\"]', '2026-08-27T10:00:00')"
    )
    db.connection.execute(
        "INSERT INTO classifications(message_id, category, source, fingerprint, cached) "
        "VALUES ('m1', 'Newsletters - other', 'rules', 'fp', 0)"
    )
    db.connection.commit()
    db.close()


def test_tui_queues_mutation_intent(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_one(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.selected_emails = [
                {
                    "id": "m1",
                    "sender_domain": "news.com",
                    "subject": "unsubscribe",
                    "labels": ["Newsletter"],
                }
            ]
            app._queue_mutation_intent(
                type(
                    "S",
                    (),
                    {
                        "action": "delete",
                        "target": "newsletters",
                        "description": "delete newsletter",
                        "email_ids": ("m1",),
                        "requires_write": True,
                    },
                )()
            )
            intents = app.database.list_mutation_intents()
            assert len(intents) == 1
            assert intents[0]["action"] == "delete"
            app.database.close()

    asyncio.run(exercise())


def test_tui_batch_categorization_undo(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_one(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            suggestion = type(
                "S",
                (),
                {
                    "action": "categorize",
                    "category": "Work",
                    "email_ids": ("m1",),
                    "requires_write": False,
                },
            )()
            app._apply_batch_categorization(suggestion, ["m1"])
            db = Database(config.database_file)
            assert db.get_user_override("m1") == ["Work"]
            db.close()
            app.action_undo_batch()
            db = Database(config.database_file)
            assert db.get_user_override("m1") is None
            db.close()
            app.database.close()

    asyncio.run(exercise())
