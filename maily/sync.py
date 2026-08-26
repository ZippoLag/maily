from __future__ import annotations

from datetime import datetime, timedelta

from .classifier import Classifier, fingerprint
from .db import Database, iso_now
from .models import ClassificationResult, ScanResult

CHUNK_SIZES = ("day", "week", "month", "year")


def split_date_range(
    start: datetime, end: datetime, chunk_size: str = "day"
) -> list[tuple[datetime, datetime]]:
    """Split [start, end] into date-based chunks (day/week/month/year)."""
    if chunk_size not in CHUNK_SIZES:
        raise ValueError(
            f"Invalid chunk size: {chunk_size} (expected one of {', '.join(CHUNK_SIZES)})"
        )
    chunks: list[tuple[datetime, datetime]] = []
    cursor = start
    while cursor <= end:
        if chunk_size == "day":
            chunk_end = cursor.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        elif chunk_size == "week":
            chunk_end = (cursor + timedelta(days=6)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        elif chunk_size == "month":
            chunk_end = (cursor.replace(day=28) + timedelta(days=4)).replace(
                day=1
            ) - timedelta(microseconds=1)
        else:  # year
            chunk_end = cursor.replace(
                month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
            )
        chunk_end = min(chunk_end, end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(microseconds=1)
    return chunks


def scan(
    gmail_client,
    database: Database,
    classifier: Classifier,
    start: datetime,
    end: datetime,
    include_read: bool = False,
    chunk_size: str = "day",
    progress_callback=None,
) -> ScanResult:
    started = iso_now()
    run_id = database.connection.execute(
        "INSERT INTO sync_runs(started_at, window_start, window_end, status) VALUES (?, ?, ?, 'running')",
        (started, start.isoformat(), end.isoformat()),
    ).lastrowid
    database.connection.commit()
    try:
        chunks = split_date_range(start, end, chunk_size)
        results: dict[str, ClassificationResult] = {}
        all_messages: list = []
        errors: list[str] = []
        total_fetched = 0
        for chunk_index, (chunk_start, chunk_end) in enumerate(chunks):
            if progress_callback:
                progress_callback(chunk_index, len(chunks), chunk_start, chunk_end)
            messages = gmail_client.fetch_messages(
                chunk_start, chunk_end, include_read=include_read
            )
            total_fetched += len(messages)
            all_messages.extend(messages)
            stored: dict[str, tuple[list[str], str, str, bool]] = {}
            for message in messages:
                message_fingerprint = fingerprint(
                    message, classifier.categories, classifier.rules
                )
                cached = database._stored_classification(
                    message.id, message_fingerprint
                )
                if cached:
                    original_categories, original_source = cached
                    result = ClassificationResult(
                        original_categories, original_source, cached=True
                    )
                else:
                    result, message_fingerprint = classifier.classify(message)
                    original_categories, original_source = (
                        result.categories,
                        result.source,
                    )
                override = database.get_user_override(message.id)
                if override is not None:
                    result = ClassificationResult(
                        override,
                        "override",
                        cached=result.cached,
                        matched_rules=result.matched_rules,
                    )
                results[message.id] = result
                stored[message.id] = (
                    original_categories,
                    original_source,
                    message_fingerprint,
                    result.cached,
                )
                if result.error:
                    errors.append(f"{message.id}: {result.error}")
            database.upsert_messages(messages, stored)
        with database.transaction() as connection:
            connection.execute(
                "UPDATE sync_runs SET completed_at=?, status='completed', error=? WHERE id=?",
                (iso_now(), "\n".join(errors) or None, run_id),
            )
        status = "degraded" if errors else "completed"
        return ScanResult(
            started,
            iso_now(),
            status,
            all_messages,
            results,
            errors,
            category_names=list(classifier.categories),
        )
    except Exception as exc:  # noqa: BLE001 - record unexpected scan failures in the sync run
        with database.transaction() as connection:
            connection.execute(
                "UPDATE sync_runs SET completed_at=?, status='failed', error=? WHERE id=?",
                (iso_now(), str(exc), run_id),
            )
        return ScanResult(
            started,
            iso_now(),
            "failed",
            errors=[str(exc)],
            category_names=list(classifier.categories),
        )
