import asyncio
from types import SimpleNamespace

from textual.widgets import ProgressBar

from maily.config import load_config
from maily.db import Database
from maily.tui import BrowseApp, CategoryEditModal, SuggestionModal, SummaryModal


def _seed(config) -> None:
    db = Database(config.database_file)
    db.seed_categories(config.categories)
    db.connection.execute("INSERT INTO threads(id) VALUES ('t1')")
    db.connection.execute(
        "INSERT INTO messages(id, thread_id, sender_name, sender_email, sender_domain, "
        "subject, body, received_at, unread, is_spam, importance, synced_at) "
        "VALUES ('m1', 't1', 'Alice', 'alice@example.com', 'example.com', 'Hello', "
        "'Body text', '2026-08-26T10:00:00', 1, 0, NULL, '2026-08-26T10:00:00')"
    )
    db.connection.execute(
        "INSERT INTO classifications(message_id, category, source, fingerprint, cached) "
        "VALUES ('m1', 'Work', 'rules', 'fp', 0)"
    )
    db.add_rule_suggestion("invoice", "Work", "m1", 0.9)
    db.connection.commit()
    db.close()


def _item() -> dict:
    return {
        "id": "m1",
        "subject": "Hello",
        "sender_name": "Alice",
        "sender_email": "alice@example.com",
        "categories": ["Work"],
        "category": "Work",
        "body": "Body text",
    }


def test_browse_app_interactions(tmp_path):
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            # Rebuild on mount populated the tree from the seeded message.
            app.on_tree_node_selected(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            assert app.selected_email is not None
            assert len(app.selected_emails) == 1

            # Mark toggles the already-selected email off, then back on.
            app.action_mark()
            assert len(app.selected_emails) == 0
            app.action_mark()
            assert len(app.selected_emails) == 1

            # Sort cycles the field and rebuilds the tree.
            app.action_sort()
            assert app.sort_field == "importance"

            # Summary modal (deterministic fallback, no inference).
            app.action_summarize()
            await pilot.pause()
            assert isinstance(app.screen, SummaryModal)
            app.screen.dismiss(None)
            await pilot.pause()

            # Suggestion modal: accept the pending suggestion, then dismiss.
            app.action_suggestions()
            await pilot.pause()
            assert isinstance(app.screen, SuggestionModal)
            app.screen.on_key(SimpleNamespace(key="a"))
            await pilot.pause()
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()

            # Category edit modal: save the checked categories.
            app.action_edit_categories()
            await pilot.pause()
            assert isinstance(app.screen, CategoryEditModal)
            app.screen.action_save()
            await pilot.pause()

            # Everything survived: tree still rebuilds.
            app.action_sort()
            await pilot.pause()

    asyncio.run(exercise())


def test_tui_shows_progress_bar_during_rebuild(tmp_path):
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            bar = app.query_one("#load-progress", ProgressBar)
            assert bar is not None
            # Rebuild drives the progress bar over the loaded groups.
            app.rebuild()
            await pilot.pause()
            # Bar is hidden again once loading completes.
            assert bar.display is False

    asyncio.run(exercise())
