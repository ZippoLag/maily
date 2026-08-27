"""Tests for keyboard-only-tui change: implicit selection via tree navigation."""

import asyncio
from types import SimpleNamespace

from maily.config import load_config
from maily.tui import BrowseApp, CategoryEditModal, SummaryModal


def _seed(config):
    """Seed one email into the database."""
    from maily.db import Database

    db = Database(config.database_file)
    db.seed_categories(tuple(config.categories))
    db.connection.execute("INSERT INTO threads(id) VALUES ('t1')")
    db.connection.execute(
        "INSERT INTO messages(id, thread_id, sender_name, sender_email, "
        "subject, body, received_at, unread, is_spam, synced_at) "
        "VALUES ('m1', 't1', 'Alice', 'alice@example.com', 'Hello', "
        "'Test body', '2026-08-27T10:00:00', 1, 0, '2026-08-27T10:00:00')"
    )
    db.connection.commit()
    db.close()


def _item():
    """Return a minimal email item dict."""
    return {
        "id": "m1",
        "subject": "Hello",
        "sender_name": "Alice",
        "sender_email": "alice@example.com",
        "category": "Work",
        "categories": ["Work"],
        "body": "Test body",
    }


def test_keyboard_navigation_sets_selected_email(tmp_path):
    """Highlighting a tree node sets selected_email to that email."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Simulate highlight on an email node
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            assert app.selected_email is not None
            assert app.selected_email["id"] == "m1"

    asyncio.run(exercise())


def test_keyboard_navigation_updates_status_bar(tmp_path):
    """Highlighting an email node updates the status bar with email info."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            status_text = app.status.content
            assert "alice@example.com" in status_text
            assert "Hello" in status_text

    asyncio.run(exercise())


def test_highlighting_category_node_does_not_update_selected_email(tmp_path):
    """Highlighting a category node (no data) clears selected_email."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            # First highlight an email
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            assert app.selected_email is not None
            # Then highlight a category node (no data)
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=None))
            )
            assert app.selected_email is None

    asyncio.run(exercise())


def test_highlight_preserves_marks(tmp_path):
    """Highlighting a different email does not clear existing marks."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Mark an email
            app.selected_email = _item()
            app.selected_emails = [_item()]
            # Highlight a different email
            other = {**_item(), "id": "m2", "subject": "Other"}
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=other))
            )
            # Marks preserved, focused email updated
            assert len(app.selected_emails) == 1
            assert app.selected_emails[0]["id"] == "m1"
            assert app.selected_email["id"] == "m2"

    asyncio.run(exercise())


def test_action_summarize_uses_focused_email(tmp_path):
    """action_summarize works on focused email without explicit selection."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Focus an email via highlight, don't mark it
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            assert app.selected_email is not None
            assert app.selected_emails == []
            # action_summarize should use the focused email
            app.action_summarize()
            await pilot.pause()
            assert isinstance(app.screen, SummaryModal)

    asyncio.run(exercise())


def test_action_mark_uses_focused_email(tmp_path):
    """action_mark works on focused email without explicit selection."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Focus an email via highlight
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            assert app.selected_email is not None
            assert app.selected_emails == []
            # action_mark should toggle the focused email
            app.action_mark()
            assert len(app.selected_emails) == 1
            assert app.selected_emails[0]["id"] == "m1"
            # Toggle again to unmark
            app.action_mark()
            assert len(app.selected_emails) == 0

    asyncio.run(exercise())


def test_action_edit_categories_uses_focused_email(tmp_path):
    """action_edit_categories opens modal for focused email."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Focus and mark an email
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            app.action_mark()
            assert len(app.selected_emails) == 1
            # action_edit_categories should open the modal
            app.action_edit_categories()
            await pilot.pause()
            assert isinstance(app.screen, CategoryEditModal)

    asyncio.run(exercise())


def test_status_bar_shows_marked_count(tmp_path):
    """Status bar shows marked count when emails are marked."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Mark an email
            app.selected_email = _item()
            app.selected_emails = [_item()]
            # Focus another email
            other = {**_item(), "id": "m2", "subject": "Other"}
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=other))
            )
            status_text = app.status.content
            assert "1 marked" in status_text
            assert "Other" in status_text

    asyncio.run(exercise())
