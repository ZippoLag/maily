from __future__ import annotations

from datetime import datetime

from .classifier import Classifier, fingerprint
from .db import Database, iso_now
from .models import ClassificationResult, ScanResult


def scan(gmail_client, database: Database, classifier: Classifier, start: datetime, end: datetime) -> ScanResult:
    started = iso_now()
    run_id = database.connection.execute(
        "INSERT INTO sync_runs(started_at, window_start, window_end, status) VALUES (?, ?, ?, 'running')",
        (started, start.isoformat(), end.isoformat()),
    ).lastrowid
    database.connection.commit()
    try:
        messages = gmail_client.today_unread(start, end)
        results: dict[str, ClassificationResult] = {}
        stored: dict[str, tuple[list[str], str, str, bool]] = {}
        errors: list[str] = []
        for message in messages:
            message_fingerprint = fingerprint(message, classifier.categories, classifier.rules)
            cached = database._stored_classification(message.id, message_fingerprint)
            if cached:
                original_categories, original_source = cached
                result = ClassificationResult(original_categories, original_source, cached=True)
            else:
                result, message_fingerprint = classifier.classify(message)
                original_categories, original_source = result.categories, result.source
            override = database.get_user_override(message.id)
            if override is not None:
                result = ClassificationResult(override, "override", cached=result.cached, matched_rules=result.matched_rules)
            results[message.id] = result
            stored[message.id] = (original_categories, original_source, message_fingerprint, result.cached)
            if result.error:
                errors.append(f"{message.id}: {result.error}")
        database.upsert_messages(messages, stored)
        with database.transaction() as connection:
            connection.execute("UPDATE sync_runs SET completed_at=?, status='completed', error=? WHERE id=?", (iso_now(), "\n".join(errors) or None, run_id))
        return ScanResult(started, iso_now(), "degraded" if errors else "completed", messages, results, errors, category_names=list(classifier.categories))
    except Exception as exc:
        with database.transaction() as connection:
            connection.execute("UPDATE sync_runs SET completed_at=?, status='failed', error=? WHERE id=?", (iso_now(), str(exc), run_id))
        return ScanResult(started, iso_now(), "failed", errors=[str(exc)], category_names=list(classifier.categories))