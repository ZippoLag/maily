import sqlite3
from pathlib import Path

from maily.config import DEFAULT_CATEGORIES, load_config
from maily.db import Database


def test_first_launch_creates_restricted_state(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    assert config.database_file.parent.exists()
    assert (config.home / "config.toml").exists()
    assert set(DEFAULT_CATEGORIES).issubset(config.categories)


def test_database_migrates_and_seeds_categories(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    assert (
        database.connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        == 8
    )
    assert (
        database.connection.execute("SELECT version FROM schema_version").fetchone()[0]
        == 3
    )
    database.close()


def test_database_creates_user_category_overrides_table(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    table = database.connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'user_category_overrides'"
    ).fetchone()
    assert table is not None
    database.close()


def test_database_creates_learned_rule_suggestions_table(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    table = database.connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'learned_rule_suggestions'"
    ).fetchone()
    assert table is not None
    columns = {
        row[1]
        for row in database.connection.execute(
            "PRAGMA table_info(learned_rule_suggestions)"
        )
    }
    assert {
        "pattern",
        "category",
        "source_message_id",
        "confidence",
        "status",
    }.issubset(columns)
    database.close()


def seed_message(database: Database, message_id: str = "m1") -> None:
    database.connection.execute("INSERT INTO threads(id) VALUES (?)", (message_id,))
    database.connection.execute(
        """INSERT INTO messages(id, thread_id, received_at, unread, is_spam, synced_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (message_id, message_id, "2026-08-26T10:00:00", 0, 0, "2026-08-26T10:00:00"),
    )
    database.connection.commit()


def test_user_override_round_trip(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    seed_message(database)
    assert database.get_user_override("m1") is None
    database.set_user_override("m1", ["Personal", "Work"])
    assert database.get_user_override("m1") == ["Personal", "Work"]
    database.close()


def test_user_override_update_replaces_categories(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    seed_message(database)
    database.set_user_override("m1", ["Personal"])
    database.set_user_override("m1", ["Work", "Action Required"])
    assert database.get_user_override("m1") == ["Work", "Action Required"]
    database.close()


def test_user_override_delete(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    seed_message(database)
    database.set_user_override("m1", ["Personal"])
    database.delete_user_override("m1")
    assert database.get_user_override("m1") is None
    database.close()


def test_rule_suggestion_lifecycle(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    assert database.get_rule_suggestions() == []
    database.add_rule_suggestion(
        "newsletter", "Newsletters - technical", confidence=0.8
    )
    suggestions = database.get_rule_suggestions()
    assert len(suggestions) == 1
    assert suggestions[0]["pattern"] == "newsletter"
    assert suggestions[0]["category"] == "Newsletters - technical"
    assert suggestions[0]["status"] == "pending"
    suggestion_id = suggestions[0]["id"]
    database.update_rule_suggestion_status(suggestion_id, "accepted")
    updated = database.get_rule_suggestions()
    assert updated[0]["status"] == "accepted"
    database.close()


def test_get_rule_suggestions_filters_by_status(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    database.add_rule_suggestion(
        "newsletter", "Newsletters - technical", confidence=0.8
    )
    database.add_rule_suggestion("invoice", "Action Required", confidence=0.6)
    assert len(database.get_rule_suggestions(status="pending")) == 2
    assert database.get_rule_suggestions(status="accepted") == []
    database.close()


def test_categorized_messages_applies_user_overrides(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    seed_message(database, "m1")
    seed_message(database, "m2")
    database.connection.execute(
        "INSERT INTO classifications(message_id, category, source, fingerprint, cached) "
        "VALUES ('m1', 'Action Required', 'deterministic', 'fp', 0)"
    )
    database.connection.execute(
        "INSERT INTO classifications(message_id, category, source, fingerprint, cached) "
        "VALUES ('m2', 'Work', 'deterministic', 'fp', 0)"
    )
    database.connection.commit()
    database.set_user_override("m1", ["Personal", "Work"])
    rows = database.categorized_messages()
    m1_rows = [row for row in rows if row["id"] == "m1"]
    assert {row["category"] for row in m1_rows} == {"Personal", "Work"}
    assert all(row["categories"] == ["Personal", "Work"] for row in m1_rows)
    m2_rows = [row for row in rows if row["id"] == "m2"]
    assert [row["category"] for row in m2_rows] == ["Work"]
    database.close()


def test_cached_classification_applies_user_override(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    seed_message(database)
    fingerprint = "fp1"
    database.connection.execute(
        "INSERT INTO classifications(message_id, category, source, fingerprint, cached) VALUES ('m1', 'Action Required', 'deterministic', ?, 0)",
        (fingerprint,),
    )
    database.connection.commit()
    assert database.cached_classification("m1", fingerprint) == (
        ["Action Required"],
        "deterministic",
    )
    database.set_user_override("m1", ["Personal"])
    assert database.cached_classification("m1", fingerprint) == (
        ["Personal"],
        "override",
    )
    database.close()


def test_existing_v1_database_migrates_without_data_loss(tmp_path: Path):
    path = tmp_path / "maily.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE schema_version (version INTEGER NOT NULL);
        CREATE TABLE categories (name TEXT PRIMARY KEY);
        CREATE TABLE threads (id TEXT PRIMARY KEY, first_received_at TEXT, last_received_at TEXT);
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
        """
    )
    connection.execute("INSERT INTO schema_version VALUES (1)")
    connection.execute("INSERT INTO categories(name) VALUES ('Work')")
    connection.execute("INSERT INTO threads(id) VALUES ('t1')")
    connection.execute(
        "INSERT INTO messages(id, thread_id, received_at, unread, is_spam, synced_at) "
        "VALUES ('m1', 't1', '2026-08-26T10:00:00', 0, 0, '2026-08-26T10:00:00')"
    )
    connection.commit()
    connection.close()

    database = Database(path)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    # Existing data preserved
    assert (
        database.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1
    )
    assert (
        database.connection.execute(
            "SELECT COUNT(*) FROM categories WHERE name = 'Work'"
        ).fetchone()[0]
        == 1
    )
    # New tables created
    for table in ("user_category_overrides", "learned_rule_suggestions"):
        row = database.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
        ).fetchone()
        assert row is not None
    # email_summaries table created by v3 migration
    row = database.connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'email_summaries'"
    ).fetchone()
    assert row is not None
    assert (
        database.connection.execute("SELECT version FROM schema_version").fetchone()[0]
        == 3
    )
    database.close()


def test_config_parses_inference_enabled_default(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    assert config.inference_enabled == False


def test_config_parses_inference_enabled_true(tmp_path: Path):
    config_dir = tmp_path / ".maily"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text("""timezone = "UTC"
[classification]
inference_enabled = true
[gmail]
oauth_client_file = ""
""")
    config = load_config(config_dir)
    assert config.inference_enabled == True


def test_generate_summary_degrades_when_cache_fails(tmp_path: Path):
    """When the summary cache table is missing, _generate_summary returns preview."""
    import asyncio
    from types import SimpleNamespace

    from maily.tui import BrowseApp

    config = load_config(tmp_path / ".maily")
    db = Database(config.database_file)
    db.seed_categories(tuple(config.categories))
    db.connection.execute("INSERT INTO threads(id) VALUES ('t1')")
    db.connection.execute(
        "INSERT INTO messages(id, thread_id, sender_name, sender_email, "
        "subject, body, received_at, unread, is_spam, synced_at) "
        "VALUES ('m1', 't1', 'Bob', 'bob@example.com', 'Re: Hello', "
        "'Long body text that exceeds two hundred characters "
        "and should be truncated in the preview output shown to the user', "
        "'2026-08-27T10:00:00', 1, 0, '2026-08-27T10:00:00')"
    )
    db.connection.commit()
    # Drop the email_summaries table to simulate a pre-v3 database
    db.connection.execute("DROP TABLE IF EXISTS email_summaries")
    db.connection.commit()
    db.close()

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test():
            email_data = {
                "id": "m1",
                "body": "Long body text that exceeds two hundred characters "
                "and should be truncated in the preview output shown to the user",
                "sender_name": "Bob",
                "sender_email": "bob@example.com",
                "subject": "Re: Hello",
            }
            result = app._generate_summary(email_data)
            assert result.startswith("Preview:")
            assert "truncated" in result

    asyncio.run(exercise())
