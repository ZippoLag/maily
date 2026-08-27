import builtins
import importlib
import sys
import tempfile
from pathlib import Path

import pytest

import maily.tui
from maily.config import DEFAULT_CATEGORIES
from maily.db import Database
from maily.tui import (
    format_category_badges,
    format_full_category_list,
    grouped_rows,
    save_category_overrides,
    suggestion_list_text,
    toggle_category,
)


def test_database_summary_cache():
    """Test that email summaries can be cached and retrieved from the database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        db = Database(db_path)

        db.store_summary("test-msg-1", "Test summary", "test-model", "test-fingerprint")
        cached = db.get_summary("test-msg-1", "test-fingerprint")
        assert cached == "Test summary"

        db.store_summary(
            "test-msg-1", "Updated summary", "test-model-2", "different-fingerprint"
        )
        cached = db.get_summary("test-msg-1", "different-fingerprint")
        assert cached == "Updated summary"

        cached = db.get_summary("nonexistent", "fingerprint")
        assert cached is None

        db.close()
    finally:
        db_path.unlink()


def test_grouped_rows_preserves_order():
    """Test that grouped_rows preserves the original order for each category."""
    rows = [
        {
            "category": "Work",
            "subject": "Older",
            "last_received_at": "2026-08-25T08:00:00",
            "importance": 1,
        },
        {
            "category": "Work",
            "subject": "Newer",
            "last_received_at": "2026-08-25T09:00:00",
            "importance": 2,
        },
        {
            "category": "Personal",
            "subject": "Test",
            "last_received_at": "2026-08-25T10:00:00",
            "importance": 3,
        },
    ]
    grouped = grouped_rows(rows, ["Work", "Personal"])

    assert [row["subject"] for row in grouped["Work"]] == ["Newer", "Older"]
    assert [row["subject"] for row in grouped["Personal"]] == ["Test"]


def test_grouped_rows_handles_empty_categories():
    """Test that grouped_rows handles empty categories correctly."""
    rows = [
        {
            "category": "Work",
            "subject": "Test",
            "last_received_at": "2026-08-25T08:00:00",
            "importance": 1,
        },
    ]
    grouped = grouped_rows(rows, ["Work", "Personal", "Other"])

    assert [row["subject"] for row in grouped["Work"]] == ["Test"]
    assert grouped["Personal"] == []
    assert grouped["Other"] == []


def test_tui_textual_imports_resolve():
    """Textual classes used by the TUI must resolve (regression: ModalScreen lives in textual.screen)."""
    from textual.screen import ModalScreen as ScreenModal

    assert maily.tui.ModalScreen is ScreenModal
    assert maily.tui.App is not None
    assert maily.tui.Tree is not None
    assert maily.tui.Vertical is not None


def test_tui_missing_textual_raises_friendly_error(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "textual" or name.startswith("textual."):
            raise ImportError("no textual installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    original_module = sys.modules.get("maily.tui")
    sys.modules.pop("maily.tui", None)
    try:
        with pytest.raises(RuntimeError, match="extra to use the TUI"):
            importlib.import_module("maily.tui")
    finally:
        # Restore the real module so later tests keep referencing it.
        if original_module is not None:
            sys.modules["maily.tui"] = original_module
        else:
            sys.modules.pop("maily.tui", None)


def test_toggle_category_adds_when_absent():
    assert toggle_category(["Work"], "Personal") == ["Work", "Personal"]


def test_toggle_category_removes_when_present():
    assert toggle_category(["Work", "Personal"], "Personal") == ["Work"]


def test_save_category_overrides_persists_for_multiple_messages():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        db = Database(db_path)
        db.seed_categories(tuple(DEFAULT_CATEGORIES))
        for message_id in ("m1", "m2"):
            db.connection.execute("INSERT INTO threads(id) VALUES (?)", (message_id,))
            db.connection.execute(
                "INSERT INTO messages(id, thread_id, received_at, unread, is_spam, synced_at) "
                "VALUES (?, ?, '2026-08-26T10:00:00', 0, 0, '2026-08-26T10:00:00')",
                (message_id, message_id),
            )
        db.connection.commit()
        save_category_overrides(db, ["m1", "m2"], ["Personal", "Work"])
        assert db.get_user_override("m1") == ["Personal", "Work"]
        assert db.get_user_override("m2") == ["Personal", "Work"]
        db.close()
    finally:
        db_path.unlink()


def test_format_category_badges_single():
    assert format_category_badges(["Work"]) == " [Work]"


def test_format_category_badges_multiple():
    assert format_category_badges(["Work", "Personal"]) == " [Work, Personal]"


def test_format_category_badges_empty():
    assert format_category_badges([]) == ""


def test_format_full_category_list_never_truncates():
    item = {
        "category": "Work",
        "categories": [
            "Work",
            "Personal",
            "Action Required",
            "Newsletters - technical",
            "Job search",
        ],
    }
    full = format_full_category_list(item)
    assert (
        full == "Work, Personal, Action Required, Newsletters - technical, Job search"
    )


def test_suggestion_list_text_shows_all_pending_suggestions():
    suggestions = [
        {"id": 1, "category": "Work", "pattern": "team", "count": 3},
        {"id": 2, "category": "Action Required", "pattern": "invoice", "count": 4},
    ]
    text = suggestion_list_text(suggestions)
    assert "1. [Work] team" in text
    assert "2. [Action Required] invoice" in text


def test_suggestion_list_text_empty():
    assert suggestion_list_text([]) == "No pending suggestions."


def test_format_full_category_list_falls_back_to_single_category():
    assert format_full_category_list({"category": "Work"}) == "Work"


def test_format_category_badges_truncates_with_more_indicator():
    assert (
        format_category_badges(["Work", "Personal", "Action Required"])
        == " [Work, Personal +1 more]"
    )


def test_save_category_overrides_empty_clears_override():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        db = Database(db_path)
        db.seed_categories(tuple(DEFAULT_CATEGORIES))
        db.connection.execute("INSERT INTO threads(id) VALUES ('m1')")
        db.connection.execute(
            "INSERT INTO messages(id, thread_id, received_at, unread, is_spam, synced_at) "
            "VALUES ('m1', 'm1', '2026-08-26T10:00:00', 0, 0, '2026-08-26T10:00:00')"
        )
        db.connection.commit()
        db.set_user_override("m1", ["Personal"])
        save_category_overrides(db, ["m1"], [])
        assert db.get_user_override("m1") is None
        db.close()
    finally:
        db_path.unlink()


def test_date_group_label_buckets():
    from datetime import UTC, datetime

    from maily.tui import date_group_label

    now = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    assert date_group_label("2026-08-26T10:00:00+00:00", now) == "Today"
    assert date_group_label("2026-08-25T10:00:00+00:00", now) == "Yesterday"
    assert date_group_label("2026-08-20T10:00:00+00:00", now) == "Last Week"
    assert date_group_label("2026-07-15T10:00:00+00:00", now) == "July 2026"
    assert date_group_label("2025-12-01T10:00:00+00:00", now) == "December 2025"


def test_generate_digest_deterministic_counts_and_themes():
    from maily.tui import generate_digest

    items = [
        {
            "subject": "Invoice attached",
            "body": "Please pay",
            "categories": ["Action Required"],
        },
        {
            "subject": "Newsletter #5",
            "body": "unsubscribe here",
            "categories": ["Newsletters - other"],
        },
        {"subject": "Team sync meeting", "body": "join", "categories": ["Work"]},
        {"subject": "Lunch plan", "body": "pizza", "categories": ["Personal"]},
    ]
    text, source = generate_digest(items)
    assert source == "deterministic"
    assert (
        "4 emails: 1 Action Required, 1 Newsletters - other, 1 Work, 1 Personal" in text
    )
    assert "1 invoice" in text
    assert "1 newsletter" in text
    assert "1 meeting request" in text


def test_generate_digest_uses_inference_when_available():
    from maily.tui import generate_digest

    items = [{"subject": "Invoice", "body": "", "categories": ["Action Required"]}]
    text, source = generate_digest(items, infer=lambda prompt: "AI digest text")
    assert source == "inference"
    assert text == "AI digest text"


def test_generate_digest_falls_back_when_inference_fails():
    from maily.tui import generate_digest

    items = [{"subject": "Invoice", "body": "", "categories": ["Action Required"]}]

    def broken(prompt):
        raise RuntimeError("ollama down")

    text, source = generate_digest(items, infer=broken)
    assert source == "deterministic"
    assert "1 emails" not in text  # singular handled
    assert "1 email: 1 Action Required" in text


def test_generate_digest_empty_view():
    from maily.tui import generate_digest

    text, source = generate_digest([])
    assert source == "deterministic"
    assert "0 emails" in text


def test_grouped_rows_handles_empty_body():
    """Test that grouped_rows handles rows with empty body."""
    rows = [
        {
            "category": "Work",
            "subject": "Test",
            "body": "",
            "last_received_at": "2026-08-25T08:00:00",
            "importance": 1,
        },
    ]
    grouped = grouped_rows(rows, ["Work", "Personal"])

    assert [row["subject"] for row in grouped["Work"]] == ["Test"]
    assert grouped["Personal"] == []
