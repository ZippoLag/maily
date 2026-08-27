from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from .classifier import Classifier, fingerprint
from .config import SCAN_CHUNK_SIZES as CHUNK_SIZES
from .db import Database, iso_now
from .models import ClassificationResult, ScanResult
from .progress import warn_on_memory

# v1 is single-account; sync state is tracked under this key until
# multi-account support lands.
SYNC_ACCOUNT = "default"

NETWORK_ERROR_HINTS = ("url", "connection", "timeout", "reset", "refused")
QUOTA_ERROR_HINTS = (
    "quota",
    "rate limit",
    "429",
    "userratelimitexceeded",
    "ratelimitexceeded",
)


def classify_error(exc: Exception) -> str:
    """Classify a sync error as network, quota, parsing, or unknown."""
    text = str(exc).lower()
    if isinstance(exc, TimeoutError):
        return "network"
    if any(hint in text for hint in QUOTA_ERROR_HINTS):
        return "quota"
    if any(hint in text for hint in NETWORK_ERROR_HINTS):
        return "network"
    return "unknown"


class ScanLock:
    """A simple exclusive lock file preventing concurrent scans.

    Only active in long-running mode; normal scans skip the lock so existing
    single-shot behavior is unchanged.
    """

    def __init__(self, path, enabled: bool = True):
        self.path = path
        self.enabled = enabled
        self._fd = None

    def __enter__(self):
        if not self.enabled:
            return self
        try:
            self._fd = self.path.open("x")
            self._fd.write(str(os.getpid()))
            self._fd.flush()
        except FileExistsError as exc:
            raise RuntimeError(
                f"Another scan appears to be running (lock file exists: {self.path}). "
                "Delete it if that scan crashed."
            ) from exc
        return self

    def __exit__(self, *exc_info):
        if self._fd is not None:
            self._fd.close()
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
        return False


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
    batch_size: int = 100,
    long_running: bool = False,
    checkpoint_emails: int = 100,
    max_retries: int = 5,
    logs_dir=None,
    memory_limit_mb: int | None = None,
) -> ScanResult:
    if batch_size < 1:
        raise ValueError(f"Invalid batch size: {batch_size} (must be >= 1)")
    started = iso_now()
    database.save_sync_state(
        status="running",
        started_at=started,
        chunk_size=chunk_size,
        total_processed=0,
        completed_at=None,
        last_sync_date=None,
    )
    run_id = database.connection.execute(
        "INSERT INTO sync_runs(started_at, window_start, window_end, status) VALUES (?, ?, ?, 'running')",
        (started, start.isoformat(), end.isoformat()),
    ).lastrowid
    database.connection.commit()
    total_fetched = 0
    checkpoint_threshold = max(1, checkpoint_emails)
    logger = None
    if logs_dir is not None:
        from .progress import JsonlLogger

        logs_dir = Path(logs_dir)
        logger = JsonlLogger(logs_dir / "scan_progress.jsonl")
    lock = ScanLock(Path(database.path).with_name("scan.lock"), enabled=long_running)
    interrupted = False
    try:
        with lock:
            return _scan_locked(
                gmail_client,
                database,
                classifier,
                start,
                end,
                include_read,
                chunk_size,
                progress_callback,
                batch_size,
                started,
                run_id,
                checkpoint_threshold,
                max_retries,
                logger,
                memory_limit_mb,
                logs_dir,
            )
    except KeyboardInterrupt:
        interrupted = True
        database.save_sync_state(
            status="failed",
            completed_at=iso_now(),
            total_processed=total_fetched,
        )
        raise
    finally:
        if interrupted:
            with database.transaction() as connection:
                connection.execute(
                    "UPDATE sync_runs SET completed_at=?, status='interrupted' WHERE id=?",
                    (iso_now(), run_id),
                )


def _scan_locked(
    gmail_client,
    database: Database,
    classifier: Classifier,
    start: datetime,
    end: datetime,
    include_read: bool,
    chunk_size: str,
    progress_callback,
    batch_size: int,
    started: str,
    run_id,
    checkpoint_threshold: int,
    max_retries: int,
    logger,
    memory_limit_mb: int | None,
    logs_dir,
) -> ScanResult:
    total_fetched = 0
    try:
        chunks = split_date_range(start, end, chunk_size)
        results: dict[str, ClassificationResult] = {}
        all_messages: list = []
        errors: list[str] = []
        for chunk_index, (chunk_start, chunk_end) in enumerate(chunks):
            try:
                messages = gmail_client.fetch_messages(
                    chunk_start, chunk_end, include_read=include_read
                )
            except Exception as exc:  # noqa: BLE001 - continue-on-error per chunk
                category = classify_error(exc)
                errors.append(f"chunk {chunk_start.date()}: {category} error: {exc}")
                if logger:
                    logger.log(event="chunk_error", kind=category, error=str(exc))
                continue
            total_fetched += len(messages)
            all_messages.extend(messages)
            chunk_cached = 0
            # Stream the chunk in batches: classify and commit each batch, then
            # drop its working set so memory stays bounded for large chunks.
            for batch_start in range(0, len(messages), batch_size):
                batch = messages[batch_start : batch_start + batch_size]
                stored: dict[str, tuple[list[str], str, str, bool]] = {}
                for message in batch:
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
                    if result.cached:
                        chunk_cached += 1
                database.upsert_messages(batch, stored)
                del stored
                if total_fetched % checkpoint_threshold < batch_size:
                    database.save_sync_state(
                        last_sync_date=chunk_end.isoformat(),
                        total_processed=total_fetched,
                    )
            if logger:
                logger.log(
                    event="chunk_done",
                    chunk_index=chunk_index,
                    total_chunks=len(chunks),
                    fetched=len(messages),
                    total_fetched=total_fetched,
                    cached=chunk_cached,
                    errors=len(errors),
                )
            warning = warn_on_memory(memory_limit_mb)
            if warning and logger:
                logger.log(event="memory_warning", message=warning)
            if progress_callback:
                progress_callback(
                    chunk_index,
                    len(chunks),
                    chunk_start,
                    chunk_end,
                    {
                        "fetched": len(messages),
                        "total_fetched": total_fetched,
                        "cached": chunk_cached,
                        "errors": len(errors),
                    },
                )
            database.save_sync_state(
                last_sync_date=chunk_end.isoformat(), total_processed=total_fetched
            )
        with database.transaction() as connection:
            connection.execute(
                "UPDATE sync_runs SET completed_at=?, status='completed', error=? WHERE id=?",
                (iso_now(), "\n".join(errors) or None, run_id),
            )
        if errors and total_fetched == 0:
            status = "failed"
        elif errors:
            status = "degraded"  # partial success: some chunks processed
        else:
            status = "completed"
        if errors and logs_dir is not None:
            log_path = Path(logs_dir) / "scan_errors.log"
            log_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write("\n".join(errors) + "\n")
        database.save_sync_state(status=status, completed_at=iso_now())
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
        database.save_sync_state(
            status="failed",
            completed_at=iso_now(),
            total_processed=total_fetched,
        )
        return ScanResult(
            started,
            iso_now(),
            "failed",
            errors=[str(exc)],
            category_names=list(classifier.categories),
        )
