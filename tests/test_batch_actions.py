"""Tests for batch-actions change: Gmail labels, multi-select, batch actions."""

import asyncio
from types import SimpleNamespace

from maily.config import load_config
from maily.db import Database
from maily.gmail import _user_labels, parse_message
from maily.models import EmailMessage
from maily.suggestions import analyze_batch, cache_key, generate_suggestions
from maily.tui import BrowseApp, format_label_badges

# ── Model (tasks 1.1, 1.2) ──────────────────────────────────────────────


def test_email_message_has_labels_field():
    message = EmailMessage(
        id="m1",
        thread_id="t1",
        sender_name="A",
        sender_email="a@example.com",
        sender_domain="example.com",
        subject="Hi",
        body="body",
        received_at=__import__("datetime").datetime(2026, 8, 27, 10, 0),
        unread=True,
        is_spam=False,
        labels=("Newsletter", "Finance"),
    )
    assert message.labels == ("Newsletter", "Finance")
    data = message.as_dict()
    assert data["labels"] == ["Newsletter", "Finance"]


def test_email_message_labels_default_to_empty():
    message = EmailMessage(
        id="m1",
        thread_id="t1",
        sender_name="A",
        sender_email="a@example.com",
        sender_domain="example.com",
        subject="Hi",
        body="body",
        received_at=__import__("datetime").datetime(2026, 8, 27, 10, 0),
        unread=True,
        is_spam=False,
    )
    assert message.labels == ()


# ── Gmail parsing (tasks 2.1, 2.2) ──────────────────────────────────────


def _raw_message(label_ids):
    return {
        "id": "m1",
        "threadId": "t1",
        "internalDate": "1756000000000",
        "labelIds": label_ids,
        "payload": {
            "headers": [
                {"name": "From", "value": "A <a@example.com>"},
                {"name": "Subject", "value": "Hi"},
            ],
            "body": {"data": "aGVsbG8="},
        },
    }


def test_parse_message_extracts_user_labels():
    message = parse_message(
        _raw_message(["INBOX", "UNREAD", "Newsletter", "Finance"]), is_spam=False
    )
    assert message.labels == ("Newsletter", "Finance")


def test_parse_message_filters_system_labels():
    message = parse_message(
        _raw_message(
            [
                "INBOX",
                "SPAM",
                "CATEGORY_PROMOTIONS",
                "IMPORTANT",
                "STARRED",
                "MyLabel",
            ]
        ),
        is_spam=False,
    )
    assert message.labels == ("MyLabel",)


def test_user_labels_helper_dedupes():
    assert _user_labels(["A", "A", "UNREAD", "B"]) == ("A", "B")
    assert _user_labels([]) == ()


# ── Database labels (tasks 1.3, 2.3) ────────────────────────────────────


def test_labels_persisted_and_returned(tmp_path):
    config = load_config(tmp_path / "home")
    db = Database(config.database_file)
    db.seed_categories(("Work",))
    message = EmailMessage(
        id="m1",
        thread_id="t1",
        sender_name="A",
        sender_email="a@example.com",
        sender_domain="example.com",
        subject="Hi",
        body="body",
        received_at=__import__("datetime").datetime(2026, 8, 27, 10, 0),
        unread=True,
        is_spam=False,
        labels=("Newsletter",),
    )
    db.upsert_messages([message], {"m1": (["Work"], "rules", "fp", False)})
    rows = db.categorized_messages()
    assert rows[0]["id"] == "m1"
    assert rows[0]["labels"] == ("Newsletter",)
    db.close()


def test_old_rows_without_labels_return_empty(tmp_path):
    config = load_config(tmp_path / "home")
    db = Database(config.database_file)
    db.seed_categories(("Work",))
    # Insert a row that predates the labels column migration path.
    db.connection.execute("INSERT INTO threads(id) VALUES ('t1')")
    db.connection.execute(
        "INSERT INTO messages(id, thread_id, sender_name, sender_email, "
        "subject, body, received_at, unread, is_spam, synced_at) "
        "VALUES ('old', 't1', '', '', 'Old', '', '2026-08-27T10:00:00', 1, 0, "
        "'2026-08-27T10:00:00')"
    )
    db.connection.execute(
        "INSERT INTO classifications(message_id, category, source, fingerprint, cached) "
        "VALUES ('old', 'Work', 'rules', 'fp', 0)"
    )
    db.connection.commit()
    rows = db.categorized_messages()
    assert rows[0]["labels"] == ()
    db.close()


# ── Label badges (tasks 4.1-4.4, 7.4) ───────────────────────────────────


def test_format_label_badges_empty():
    assert format_label_badges([]) == ""
    assert format_label_badges(None) == ""


def test_format_label_badges_shows_labels_with_truncation():
    rendered = format_label_badges(["Newsletter", "Finance", "Receipts"])
    assert "Newsletter" in rendered
    assert "Finance" in rendered
    assert "+1 more" in rendered
    assert "Receipts" not in rendered


# ── TUI multi-select (tasks 3.1-3.8, 7.1-7.3) ───────────────────────────


def _seed_multi(config, count=3):
    db = Database(config.database_file)
    db.seed_categories(tuple(config.categories))
    for i in range(count):
        db.connection.execute("INSERT INTO threads(id) VALUES (?)", (f"t{i}",))
        db.connection.execute(
            "INSERT INTO messages(id, thread_id, sender_name, sender_email, "
            "subject, body, received_at, unread, is_spam, labels, synced_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, ?, '2026-08-27T10:00:00')",
            (
                f"m{i}",
                f"t{i}",
                f"Sender {i}",
                f"s{i}@example.com",
                f"Subj {i}",
                "body",
                "2026-08-27T10:00:00",
                '["Newsletter"]' if i % 2 else "[]",
            ),
        )
        db.connection.execute(
            "INSERT INTO classifications(message_id, category, source, fingerprint, cached) "
            "VALUES (?, 'Work', 'rules', 'fp', 0)",
            (f"m{i}",),
        )
    db.connection.commit()
    db.close()


def _item(mid="m0"):
    return {
        "id": mid,
        "subject": f"Subj {int(mid[1:])}",
        "sender_name": f"Sender {int(mid[1:])}",
        "sender_email": f"s{int(mid[1:])}@example.com",
        "category": "Work",
        "categories": ["Work"],
        "labels": ("Newsletter",) if int(mid[1:]) % 2 else (),
    }


def test_space_toggles_selection(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_multi(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.selected_email = _item("m0")
            app.action_toggle_select()
            assert len(app.selected_emails) == 1
            app.action_toggle_select()
            assert len(app.selected_emails) == 0

    asyncio.run(exercise())


def test_select_all_and_deselect_all_visible(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_multi(config, count=3)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_select_all_visible()
            assert len(app.selected_emails) >= 1
            app.action_deselect_all()
            assert app.selected_emails == []

    asyncio.run(exercise())


def test_selection_persists_across_sort(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_multi(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            item = _item("m0")
            app.selected_emails = [item]
            app.action_sort()
            assert any(e["id"] == "m0" for e in app.selected_emails)

    asyncio.run(exercise())


def test_filter_by_label_toggles(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_multi(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.selected_email = _item("m1")
            app.action_filter_by_label()
            assert app._label_filter == "Newsletter"
            app.action_filter_by_label()
            assert app._label_filter is None

    asyncio.run(exercise())


# ── Batch categorization (tasks 5.1-5.6, 7.6-7.7) ───────────────────────


def test_batch_categorization_applies_to_all_selected(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_multi(config, count=3)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.selected_emails = [_item("m0"), _item("m1")]
            suggestion = SimpleNamespace(
                action="categorize", category="Personal", email_ids=("m0", "m1")
            )
            app._apply_batch_categorization(suggestion, ["m0", "m1"])
            db = Database(config.database_file)
            assert db.get_user_override("m0") == ["Personal"]
            assert db.get_user_override("m1") == ["Personal"]
            db.close()

    asyncio.run(exercise())


def test_category_edit_modal_requires_confirmation_for_batch(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_multi(config, count=3)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            from maily.tui import CategoryEditModal

            modal = CategoryEditModal(list(config.categories), ["Work"], ["m0", "m1"])
            await app.push_screen(modal)
            await pilot.pause()
            modal.action_save()
            assert modal.confirming is True
            modal.on_key(SimpleNamespace(key="y"))
            await pilot.pause()

    asyncio.run(exercise())


# ── Suggestions (tasks 6.1-6.8, 7.8-7.10) ───────────────────────────────


def test_analyze_batch_groups_by_sender_domain_label():
    emails = [
        {
            "id": "a",
            "sender_name": "X",
            "sender_domain": "x.com",
            "labels": ["N"],
            "category": "Work",
        },
        {
            "id": "b",
            "sender_name": "X",
            "sender_domain": "x.com",
            "labels": ["N"],
            "category": "Work",
        },
        {
            "id": "c",
            "sender_name": "Y",
            "sender_domain": "y.com",
            "labels": [],
            "category": "Other",
        },
    ]
    summary = analyze_batch(emails)
    assert summary["senders"]["X"] == 2
    assert summary["domains"]["x.com"] == 2
    assert summary["labels"]["N"] == 2


def test_generate_suggestions_deterministic():
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
    suggestions = generate_suggestions(emails)
    actions = {s.action for s in suggestions}
    assert "categorize" in actions
    assert "delete" in actions
    # Mutations are read-only suggestions.
    for s in suggestions:
        if s.action in ("delete", "archive", "mark-read"):
            assert s.requires_write is True
        else:
            assert s.requires_write is False


def test_suggestions_confidence_bounded():
    emails = [
        {
            "id": f"m{i}",
            "sender_name": "Same",
            "sender_domain": "d.com",
            "category": "Work",
            "labels": [],
        }
        for i in range(8)
    ]
    suggestions = generate_suggestions(emails)
    for s in suggestions:
        assert 0.0 <= s.confidence <= 0.95


def test_inference_suggestions_used_when_available():
    emails = [
        {
            "id": f"m{i}",
            "sender_name": "X",
            "sender_domain": "x.com",
            "category": "Work",
            "labels": [],
        }
        for i in range(2)
    ]
    seen = {}

    def fake_infer(prompt: str) -> str:
        seen["called"] = True
        return "categorize: invoices (2 emails)"

    suggestions = generate_suggestions(emails, infer=fake_infer)
    assert seen.get("called") is True
    assert any(s.description.startswith("categorize: invoices") for s in suggestions)


def test_inference_failure_falls_back_to_deterministic():
    emails = [
        {
            "id": f"m{i}",
            "sender_name": "News",
            "sender_domain": "news.com",
            "subject": "unsubscribe",
            "labels": [],
            "category": "Newsletters - other",
        }
        for i in range(3)
    ]

    def broken_infer(prompt: str) -> str:
        raise RuntimeError("down")

    suggestions = generate_suggestions(emails, infer=broken_infer)
    assert any(s.action == "delete" for s in suggestions)


def test_suggestion_cache_key_stable():
    a = [{"id": "b"}, {"id": "a"}]
    b = [{"id": "a"}, {"id": "b"}]
    assert cache_key(a) == cache_key(b)
