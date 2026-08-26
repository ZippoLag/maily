from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 1


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.migrate()

    def migrate(self) -> None:
        self.connection.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
        row = self.connection.execute("SELECT version FROM schema_version").fetchone()
        current = row[0] if row else 0
        if current > SCHEMA_VERSION:
            raise RuntimeError(f"Database version {current} is newer than supported version {SCHEMA_VERSION}")
        if current < 1:
            with self.connection:
                self.connection.executescript(
                    """
                    CREATE TABLE accounts (
                        id INTEGER PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        credential_key TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE threads (
                        id TEXT PRIMARY KEY,
                        first_received_at TEXT,
                        last_received_at TEXT
                    );
                    CREATE TABLE messages (
                        id TEXT PRIMARY KEY,
                        thread_id TEXT NOT NULL REFERENCES threads(id),
                        sender_name TEXT NOT NULL DEFAULT '',
                        sender_email TEXT NOT NULL DEFAULT '',
                        sender_domain TEXT NOT NULL DEFAULT '',
                        subject TEXT NOT NULL DEFAULT '',
                        body TEXT NOT NULL DEFAULT '',
                        received_at TEXT NOT NULL,
                        unread INTEGER NOT NULL,
                        is_spam INTEGER NOT NULL,
                        importance REAL,
                        synced_at TEXT NOT NULL
                    );
                    CREATE TABLE categories (
                        name TEXT PRIMARY KEY
                    );
                    CREATE TABLE classifications (
                        message_id TEXT NOT NULL REFERENCES messages(id),
                        category TEXT NOT NULL REFERENCES categories(name),
                        source TEXT NOT NULL,
                        fingerprint TEXT NOT NULL,
                        cached INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (message_id, category)
                    );
                    CREATE TABLE sync_runs (
                        id INTEGER PRIMARY KEY,
                        started_at TEXT NOT NULL,
                        completed_at TEXT,
                        window_start TEXT NOT NULL,
                        window_end TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error TEXT
                    );
                    CREATE TABLE action_history (
                        id INTEGER PRIMARY KEY,
                        message_id TEXT,
                        action TEXT NOT NULL,
                        details TEXT NOT NULL DEFAULT '{}',
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE email_summaries (
                        message_id TEXT PRIMARY KEY,
                        summary TEXT NOT NULL,
                        model TEXT NOT NULL DEFAULT '',
                        fingerprint TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE INDEX messages_received_idx ON messages(received_at);
                    CREATE INDEX messages_thread_idx ON messages(thread_id);
                    CREATE INDEX summaries_message_idx ON email_summaries(message_id);
                    """
                )
                self.connection.execute("INSERT INTO schema_version VALUES (1)")

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def seed_categories(self, categories: tuple[str, ...]) -> None:
        with self.transaction() as connection:
            connection.executemany("INSERT OR IGNORE INTO categories(name) VALUES (?)", [(name,) for name in categories])

    def upsert_messages(self, messages, classifications: dict[str, tuple[list[str], str, str, bool]]) -> None:
        with self.transaction() as connection:
            for message in messages:
                connection.execute(
                    """INSERT INTO threads(id, first_received_at, last_received_at) VALUES (?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET first_received_at = MIN(first_received_at, excluded.first_received_at),
                       last_received_at = MAX(last_received_at, excluded.last_received_at)""",
                    (message.thread_id, message.received_at.isoformat(), message.received_at.isoformat()),
                )
                connection.execute(
                    """INSERT INTO messages(id, thread_id, sender_name, sender_email, sender_domain, subject, body,
                       received_at, unread, is_spam, importance, synced_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET thread_id=excluded.thread_id, sender_name=excluded.sender_name,
                       sender_email=excluded.sender_email, sender_domain=excluded.sender_domain, subject=excluded.subject,
                       body=excluded.body, received_at=excluded.received_at, unread=excluded.unread,
                       is_spam=excluded.is_spam, importance=excluded.importance, synced_at=excluded.synced_at""",
                    (message.id, message.thread_id, message.sender_name, message.sender_email, message.sender_domain,
                     message.subject, message.body, message.received_at.isoformat(), message.unread, message.is_spam,
                     message.importance, iso_now()),
                )
                connection.execute("DELETE FROM classifications WHERE message_id = ?", (message.id,))
                category_names, source, message_fingerprint, cached = classifications.get(message.id, ([], "", "", False))
                for category in category_names:
                    connection.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (category,))
                    connection.execute(
                        "INSERT INTO classifications(message_id, category, source, fingerprint, cached) VALUES (?, ?, ?, ?, ?)",
                        (message.id, category, source, message_fingerprint, cached),
                    )

    def last_completed_sync(self):
        return self.connection.execute(
            "SELECT * FROM sync_runs WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        ).fetchone()

    def cached_classification(self, message_id: str, message_fingerprint: str):
        rows = self.connection.execute(
            "SELECT category, source FROM classifications WHERE message_id = ? AND fingerprint = ?",
            (message_id, message_fingerprint),
        ).fetchall()
        if not rows:
            return None
        return [row[0] for row in rows], rows[0][1]

    def categorized_messages(self):
        return self.connection.execute(
                """SELECT m.id, m.subject, m.sender_name, m.sender_email, m.sender_domain,
                    m.received_at, m.importance, t.first_received_at, t.last_received_at, c.category
                    FROM messages m JOIN threads t ON t.id = m.thread_id
                    JOIN classifications c ON c.message_id = m.id
               ORDER BY m.received_at DESC"""
        ).fetchall()

    def get_summary(self, message_id: str, fingerprint: str) -> str | None:
        """Get cached summary for a message if it exists."""
        row = self.connection.execute(
            "SELECT summary FROM email_summaries WHERE message_id = ? AND fingerprint = ?",
            (message_id, fingerprint),
        ).fetchone()
        return row[0] if row else None

    def store_summary(self, message_id: str, summary: str, model: str = "", fingerprint: str = "") -> None:
        """Store a summary for a message."""
        with self.transaction() as connection:
            connection.execute(
                """INSERT INTO email_summaries(message_id, summary, model, fingerprint, created_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(message_id) DO UPDATE SET
                   summary = excluded.summary, model = excluded.model,
                   fingerprint = excluded.fingerprint, created_at = excluded.created_at""",
                (message_id, summary, model, fingerprint, iso_now()),
            )

    def close(self) -> None:
        self.connection.close()


def iso_now() -> str:
    return datetime.now().astimezone().isoformat()


def json_details(value: dict) -> str:
    return json.dumps(value, sort_keys=True)