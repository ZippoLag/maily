from datetime import datetime, timezone

from maily.classifier import Classifier
from maily.config import DEFAULT_CATEGORIES, load_config
from maily.db import Database
from maily.learning import generate_suggestions
from maily.models import EmailMessage, primary_category
from maily.sync import scan
from maily.tui import format_category_badges, save_category_overrides


class FakeGmail:
    def __init__(self, messages):
        self.messages = messages

    def today_unread(self, start, end):
        return self.messages


def make_message(message_id: str, subject: str, sender_email: str = "person@example.com") -> EmailMessage:
    return EmailMessage(
        message_id, message_id, "", sender_email, sender_email.split("@")[-1],
        subject, "", datetime.now(timezone.utc), True, False,
    )


def test_user_rule_in_config_classifies_email(tmp_path):
    config_dir = tmp_path / ".maily"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        """timezone = "UTC"
[classification]
inference_enabled = false

[[classification.rules]]
category = "Personal"
patterns = ["family", "weekend"]

[gmail]
oauth_client_file = ""
"""
    )
    config = load_config(config_dir)
    message = make_message("m1", "Family weekend plans")
    result, _ = Classifier(config.categories, rules=config.rules).classify(message)
    assert "Personal" in result.categories
    assert result.source == "deterministic"


def test_user_override_persists_across_scans(tmp_path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    message = make_message("m1", "Your verification code", "alerts@example.com")
    bounds = config.local_today_bounds()
    scan(FakeGmail([message]), database, Classifier(tuple(DEFAULT_CATEGORIES)), *bounds)
    save_category_overrides(database, ["m1"], ["Personal", "Work"])
    second = scan(FakeGmail([message]), database, Classifier(tuple(DEFAULT_CATEGORIES)), *bounds)
    assert second.classifications["m1"].categories == ["Personal", "Work"]
    assert second.classifications["m1"].source == "override"
    rows = database.categorized_messages()
    m1_rows = [row for row in rows if row["id"] == "m1"]
    assert {row["category"] for row in m1_rows} == {"Personal", "Work"}
    database.close()


def test_rule_learning_suggests_pattern_from_corrections(tmp_path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    for message_id, subject in (
        ("m1", "Newsletter: product update"),
        ("m2", "Newsletter digest"),
        ("m3", "Newsletter preview"),
    ):
        database.connection.execute("INSERT INTO threads(id) VALUES (?)", (message_id,))
        database.connection.execute(
            "INSERT INTO messages(id, thread_id, subject, body, received_at, unread, is_spam, synced_at) "
            "VALUES (?, ?, ?, '', '2026-08-26T10:00:00', 0, 0, '2026-08-26T10:00:00')",
            (message_id, message_id, subject),
        )
    database.connection.commit()
    save_category_overrides(database, ["m1", "m2", "m3"], ["Newsletters - technical"])
    suggestions = generate_suggestions(database)
    matching = [s for s in suggestions if s["category"] == "Newsletters - technical" and s["pattern"] == "newsletter"]
    assert matching and matching[0]["count"] == 3
    database.close()


def test_multi_category_display_shows_primary_and_badges():
    categories = ["Action Required", "Work", "Personal"]
    primary = primary_category(categories)
    badges = format_category_badges([c for c in categories if c != primary])
    assert primary == "Action Required"
    assert badges == " [Work, Personal]"


def test_system_works_with_inference_disabled(tmp_path):
    config = load_config(tmp_path / ".maily")
    assert not config.inference_enabled
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    messages = [
        make_message("m1", "Your verification code", "alerts@example.com"),
        make_message("m2", "Hello world"),
    ]
    result = scan(FakeGmail(messages), database, Classifier(tuple(DEFAULT_CATEGORIES)), *config.local_today_bounds())
    assert result.status in ("completed", "degraded")
    assert result.classifications["m1"].categories == ["Action Required"]
    assert result.classifications["m2"].categories == ["Other"]
    assert all(
        classification.error is None or "provider" in classification.error
        for classification in result.classifications.values()
    )
    database.close()
