from __future__ import annotations

import collections
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 5


class Database:
    def __init__(self, path: Path, body_cache_size: int = 500):
        self.path = path
        self.body_cache_size = max(0, body_cache_size)
        self._body_cache: collections.OrderedDict[str, str] = collections.OrderedDict()
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.migrate()

    def migrate(self) -> None:
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
        )
        row = self.connection.execute("SELECT version FROM schema_version").fetchone()
        current = row[0] if row else 0
        if current > SCHEMA_VERSION:
            raise RuntimeError(
                f"Database version {current} is newer than supported version {SCHEMA_VERSION}"
            )
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
                current = 1
        if current < 2:
            with self.connection:
                self.connection.executescript(
                    """
                    CREATE TABLE user_category_overrides (
                        message_id TEXT PRIMARY KEY REFERENCES messages(id),
                        categories TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE TABLE learned_rule_suggestions (
                        id INTEGER PRIMARY KEY,
                        pattern TEXT NOT NULL,
                        category TEXT NOT NULL,
                        source_message_id TEXT REFERENCES messages(id),
                        confidence REAL NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    """
                )
                self.connection.execute("UPDATE schema_version SET version = 2")
        if current < 3:
            with self.connection:
                self.connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS sync_state (
                        account TEXT PRIMARY KEY,
                        last_sync_date TEXT,
                        last_sync_email_id TEXT,
                        total_processed INTEGER NOT NULL DEFAULT 0,
                        status TEXT NOT NULL DEFAULT 'idle',
                        started_at TEXT,
                        completed_at TEXT,
                        chunk_size TEXT NOT NULL DEFAULT 'day'
                    );
                    CREATE TABLE IF NOT EXISTS email_summaries (
                        message_id TEXT PRIMARY KEY,
                        summary TEXT NOT NULL,
                        model TEXT NOT NULL DEFAULT '',
                        fingerprint TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS summaries_message_idx ON email_summaries(message_id);
                    """
                )
                self.connection.execute("UPDATE schema_version SET version = 3")
        if current < 4:
            with self.connection:
                # User-created Gmail labels rendered as badges in the TUI.
                self.connection.execute(
                    "ALTER TABLE messages ADD COLUMN labels TEXT NOT NULL DEFAULT ''"
                )
                self.connection.execute("UPDATE schema_version SET version = 4")
        if current < 5:
            with self.connection:
                # Accepted-but-unexecuted Gmail mutation suggestions (read-only
                # until write scopes land).
                self.connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS mutation_intents (
                        id INTEGER PRIMARY KEY,
                        action TEXT NOT NULL,
                        target TEXT NOT NULL DEFAULT '',
                        description TEXT NOT NULL DEFAULT '',
                        message_ids TEXT NOT NULL DEFAULT '[]',
                        created_at TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending'
                    );
                    """
                )
                self.connection.execute("UPDATE schema_version SET version = 5")

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
            connection.executemany(
                "INSERT OR IGNORE INTO categories(name) VALUES (?)",
                [(name,) for name in categories],
            )

    def get_user_override(self, message_id: str) -> list[str] | None:
        row = self.connection.execute(
            "SELECT categories FROM user_category_overrides WHERE message_id = ?",
            (message_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def set_user_override(self, message_id: str, categories: list[str]) -> None:
        now = iso_now()
        with self.transaction() as connection:
            connection.execute(
                """INSERT INTO user_category_overrides(message_id, categories, created_at, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(message_id) DO UPDATE SET
                   categories = excluded.categories, updated_at = excluded.updated_at""",
                (message_id, json.dumps(categories), now, now),
            )

    def delete_user_override(self, message_id: str) -> None:
        with self.transaction() as connection:
            connection.execute(
                "DELETE FROM user_category_overrides WHERE message_id = ?",
                (message_id,),
            )

    def get_rule_suggestions(self, status: str | None = None) -> list[sqlite3.Row]:
        if status is None:
            return self.connection.execute(
                "SELECT * FROM learned_rule_suggestions ORDER BY id"
            ).fetchall()
        return self.connection.execute(
            "SELECT * FROM learned_rule_suggestions WHERE status = ? ORDER BY id",
            (status,),
        ).fetchall()

    def add_rule_suggestion(
        self,
        pattern: str,
        category: str,
        source_message_id: str | None = None,
        confidence: float = 0.0,
    ) -> None:
        with self.transaction() as connection:
            connection.execute(
                """INSERT INTO learned_rule_suggestions(
                   pattern, category, source_message_id, confidence, status, created_at)
                   VALUES (?, ?, ?, ?, 'pending', ?)""",
                (pattern, category, source_message_id, confidence, iso_now()),
            )

    def update_rule_suggestion_status(self, suggestion_id: int, status: str) -> None:
        with self.transaction() as connection:
            connection.execute(
                "UPDATE learned_rule_suggestions SET status = ? WHERE id = ?",
                (status, suggestion_id),
            )

    def upsert_messages(
        self, messages, classifications: dict[str, tuple[list[str], str, str, bool]]
    ) -> None:
        with self.transaction() as connection:
            for message in messages:
                connection.execute(
                    """INSERT INTO threads(id, first_received_at, last_received_at) VALUES (?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET first_received_at = MIN(first_received_at, excluded.first_received_at),
                       last_received_at = MAX(last_received_at, excluded.last_received_at)""",
                    (
                        message.thread_id,
                        message.received_at.isoformat(),
                        message.received_at.isoformat(),
                    ),
                )
                connection.execute(
                    """INSERT INTO messages(id, thread_id, sender_name, sender_email, sender_domain, subject, body,
                       received_at, unread, is_spam, importance, labels, synced_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET thread_id=excluded.thread_id, sender_name=excluded.sender_name,
                       sender_email=excluded.sender_email, sender_domain=excluded.sender_domain, subject=excluded.subject,
                       body=excluded.body, received_at=excluded.received_at, unread=excluded.unread,
                       is_spam=excluded.is_spam, importance=excluded.importance, labels=excluded.labels,
                       synced_at=excluded.synced_at""",
                    (
                        message.id,
                        message.thread_id,
                        message.sender_name,
                        message.sender_email,
                        message.sender_domain,
                        message.subject,
                        message.body,
                        message.received_at.isoformat(),
                        message.unread,
                        message.is_spam,
                        message.importance,
                        json.dumps(list(getattr(message, "labels", ()))),
                        iso_now(),
                    ),
                )
                connection.execute(
                    "DELETE FROM classifications WHERE message_id = ?", (message.id,)
                )
                category_names, source, message_fingerprint, cached = (
                    classifications.get(message.id, ([], "", "", False))
                )
                for category in category_names:
                    connection.execute(
                        "INSERT OR IGNORE INTO categories(name) VALUES (?)", (category,)
                    )
                    connection.execute(
                        "INSERT INTO classifications(message_id, category, source, fingerprint, cached) VALUES (?, ?, ?, ?, ?)",
                        (message.id, category, source, message_fingerprint, cached),
                    )

    def get_sync_state(self, account: str = "default") -> dict | None:
        """Return the sync state row for an account, or None if never tracked."""
        row = self.connection.execute(
            "SELECT * FROM sync_state WHERE account = ?", (account,)
        ).fetchone()
        return dict(row) if row else None

    def save_sync_state(
        self,
        account: str = "default",
        *,
        last_sync_date: str | None = None,
        last_sync_email_id: str | None = None,
        total_processed: int | None = None,
        status: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
        chunk_size: str | None = None,
    ) -> None:
        """Upsert sync state for an account, updating only the provided fields."""
        fields = {
            name: value
            for name, value in {
                "last_sync_date": last_sync_date,
                "last_sync_email_id": last_sync_email_id,
                "total_processed": total_processed,
                "status": status,
                "started_at": started_at,
                "completed_at": completed_at,
                "chunk_size": chunk_size,
            }.items()
            if value is not None
        }
        if not fields:
            return
        columns = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
        updates = ", ".join(f"{name} = excluded.{name}" for name in fields)
        with self.transaction() as connection:
            connection.execute(
                f"INSERT INTO sync_state(account, {columns}) VALUES (?, {placeholders}) "
                f"ON CONFLICT(account) DO UPDATE SET {updates}",
                [account, *fields.values()],
            )

    def reset_sync_state(self, account: str = "default") -> None:
        """Delete all sync state for an account so the next scan starts fresh."""
        with self.transaction() as connection:
            connection.execute("DELETE FROM sync_state WHERE account = ?", (account,))

    def last_completed_sync(self):
        return self.connection.execute(
            "SELECT * FROM sync_runs WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        ).fetchone()

    def _stored_classification(self, message_id: str, message_fingerprint: str):
        """Raw stored classification for a message, without applying user overrides."""
        rows = self.connection.execute(
            "SELECT category, source FROM classifications WHERE message_id = ? AND fingerprint = ?",
            (message_id, message_fingerprint),
        ).fetchall()
        if not rows:
            return None
        return [row[0] for row in rows], rows[0][1]

    def cached_classification(self, message_id: str, message_fingerprint: str):
        """Effective cached classification, applying a user override when present."""
        stored = self._stored_classification(message_id, message_fingerprint)
        if stored is None:
            return None
        categories, source = stored
        override = self.get_user_override(message_id)
        if override is not None:
            return override, "override"
        return categories, source

    def categorized_messages(self):
        rows = self.connection.execute(
            """SELECT m.id, m.subject, m.sender_name, m.sender_email, m.sender_domain,
                    m.body, m.received_at, m.importance, m.labels, t.first_received_at, t.last_received_at, c.category
                    FROM messages m JOIN threads t ON t.id = m.thread_id
                    JOIN classifications c ON c.message_id = m.id
               ORDER BY m.received_at DESC"""
        ).fetchall()
        by_message: dict[str, list[dict]] = {}
        for row in rows:
            item = dict(row)
            try:
                item["labels"] = tuple(json.loads(item["labels"] or "[]"))
            except (ValueError, TypeError):
                item["labels"] = ()
            by_message.setdefault(item["id"], []).append(item)
        result: list[dict] = []
        for message_id, message_rows in by_message.items():
            override = self.get_user_override(message_id)
            categories = (
                override
                if override is not None
                else [r["category"] for r in message_rows]
            )
            for category in categories:
                row = dict(message_rows[0])
                row["category"] = category
                row["categories"] = categories
                result.append(row)
        return result

    def get_message_body(self, message_id: str) -> str:
        """Return the stored body for a message (empty string when unknown).

        Bodies are cached with an LRU eviction policy sized by
        *body_cache_size* so repeated reads in the TUI stay cheap without
        holding every message body in memory.
        """
        cached = self._body_cache.get(message_id)
        if cached is not None:
            self._body_cache.move_to_end(message_id)
            return cached
        row = self.connection.execute(
            "SELECT body FROM messages WHERE id = ?", (message_id,)
        ).fetchone()
        body = row[0] if row else ""
        if self.body_cache_size > 0:
            self._body_cache[message_id] = body
            self._body_cache.move_to_end(message_id)
            while len(self._body_cache) > self.body_cache_size:
                self._body_cache.popitem(last=False)
        return body

    def get_summary(self, message_id: str, fingerprint: str) -> str | None:
        """Get cached summary for a message if it exists."""
        row = self.connection.execute(
            "SELECT summary FROM email_summaries WHERE message_id = ? AND fingerprint = ?",
            (message_id, fingerprint),
        ).fetchone()
        return row[0] if row else None

    def store_summary(
        self, message_id: str, summary: str, model: str = "", fingerprint: str = ""
    ) -> None:
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

    def save_mutation_intent(
        self,
        action: str,
        message_ids: list[str],
        target: str = "",
        description: str = "",
    ) -> int:
        """Record an accepted mutation suggestion as a pending intent."""
        with self.transaction() as connection:
            cursor = connection.execute(
                """INSERT INTO mutation_intents(action, target, description, message_ids, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (action, target, description, json.dumps(message_ids), iso_now()),
            )
            lastrowid = cursor.lastrowid
            assert lastrowid is not None
            return lastrowid

    def list_mutation_intents(self, status: str = "pending") -> list[dict]:
        rows = self.connection.execute(
            "SELECT * FROM mutation_intents WHERE status = ? ORDER BY id", (status,)
        ).fetchall()
        intents = [dict(row) for row in rows]
        for intent in intents:
            try:
                intent["message_ids"] = json.loads(intent["message_ids"] or "[]")
            except (ValueError, TypeError):
                intent["message_ids"] = []
        return intents

    def clear_mutation_intents(self, ids: list[int] | None = None) -> None:
        with self.transaction() as connection:
            if ids:
                placeholders = ",".join("?" for _ in ids)
                connection.execute(
                    f"DELETE FROM mutation_intents WHERE id IN ({placeholders})", ids
                )
            else:
                connection.execute("DELETE FROM mutation_intents")

    def record_action(
        self, message_id: str, action: str, details: dict | None = None
    ) -> None:
        """Append an action-history entry (e.g. an applied batch suggestion)."""
        with self.transaction() as connection:
            connection.execute(
                """INSERT INTO action_history(message_id, action, details, created_at)
                   VALUES (?, ?, ?, ?)""",
                (message_id, action, json_details(details or {}), iso_now()),
            )

    def close(self) -> None:
        self.connection.close()


def iso_now() -> str:
    return datetime.now().astimezone().isoformat()


def json_details(value: dict) -> str:
    return json.dumps(value, sort_keys=True)
