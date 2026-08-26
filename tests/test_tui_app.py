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


def _seed_many(config, count: int, days_ago: int = 0) -> None:
    db = Database(config.database_file)
    db.seed_categories(config.categories)
    rows = []
    for i in range(count):
        mid = f"m{i}"
        rows.append(
            (mid, mid, "Sender", "s@example.com", "example.com", f"Subj {i}", "", 0, 0)
        )
    db.connection.executemany(
        "INSERT INTO threads(id, first_received_at, last_received_at) VALUES (?, ?, ?)",
        [(mid, "2026-08-26T10:00:00", "2026-08-26T10:00:00") for mid, *_ in rows],
    )
    db.connection.executemany(
        "INSERT INTO messages(id, thread_id, sender_name, sender_email, sender_domain, "
        "subject, body, received_at, unread, is_spam, importance, synced_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, NULL, '2026-08-26T10:00:00')",
        [
            (mid, tid, name, email, dom, subj, body, "2026-08-26T10:00:00")
            for mid, tid, name, email, dom, subj, body, _, _ in rows
        ],
    )
    db.connection.executemany(
        "INSERT INTO classifications(message_id, category, source, fingerprint, cached) "
        "VALUES (?, 'Work', 'rules', 'fp', 0)",
        [(mid,) for mid, *_ in rows],
    )
    db.connection.commit()
    db.close()


def _first_email_node(tree):
    """Return the first email node in the populated category."""
    for category in tree.root.children:
        for bucket in category.children:
            for email in bucket.children:
                return email
    raise AssertionError("no email node found")


def test_tree_does_not_load_bodies_upfront(tmp_path):
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            tree = app.query_one("#tree")
            email_node = _first_email_node(tree)
            assert email_node is not None
            assert len(email_node.children) == 0  # body not loaded upfront

    asyncio.run(exercise())


def test_expanding_email_loads_body_lazily(tmp_path):
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            tree = app.query_one("#tree")
            await pilot.pause()
            email_node = _first_email_node(tree)
            assert len(email_node.children) == 0
            email_node.expand()
            await pilot.pause()
            assert len(email_node.children) == 2
            body_text = "".join(str(child.label) for child in email_node.children)
            assert "Body text" in body_text
            assert "From:" in body_text

    asyncio.run(exercise())


def test_rebuild_shows_result_count(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_many(config, 3)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            tree = app.query_one("#tree")
            assert "3" in str(tree.root.label)
            assert app.email_count == 3

    asyncio.run(exercise())


def test_keyboard_navigation_scrolls_tree(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_many(config, 200)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            tree = app.query_one("#tree")
            tree.scroll_home(animate=False)
            await pilot.pause()
            assert tree.scroll_offset.y == 0
            app.action_end()
            await pilot.pause()
            assert tree.scroll_offset.y > 0
            top = tree.scroll_offset.y
            app.action_page_up()
            await pilot.pause()
            assert tree.scroll_offset.y < top

    asyncio.run(exercise())


def test_emails_grouped_by_date_in_tree(tmp_path):
    from datetime import UTC, datetime, timedelta

    config = load_config(tmp_path / "home")
    db = Database(config.database_file)
    db.seed_categories(config.categories)
    now = datetime.now(UTC)
    dates = {
        "today": (now - timedelta(hours=1)).isoformat(),
        "yesterday": (now - timedelta(days=1, hours=1)).isoformat(),
        "old": (now - timedelta(days=40)).isoformat(),
    }
    for i, (key, received) in enumerate(dates.items()):
        mid = f"m-{key}"
        db.connection.execute("INSERT INTO threads(id) VALUES (?)", (mid,))
        db.connection.execute(
            "INSERT INTO messages(id, thread_id, sender_name, sender_email, sender_domain, "
            "subject, body, received_at, unread, is_spam, importance, synced_at) "
            "VALUES (?, ?, 'S', 's@e.com', 'e.com', ?, '', ?, 1, 0, NULL, '2026-08-26T10:00:00')",
            (mid, mid, f"Subj {key}", received),
        )
        db.connection.execute(
            "INSERT INTO classifications(message_id, category, source, fingerprint, cached) "
            "VALUES (?, 'Work', 'rules', 'fp', 0)",
            (mid,),
        )
    db.connection.commit()
    db.close()

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            tree = app.query_one("#tree")
            category_node = next(c for c in tree.root.children if c.children)
            bucket_labels = [str(child.label) for child in category_node.children]
            assert any(label.startswith("Today") for label in bucket_labels)
            assert any(label.startswith("Yesterday") for label in bucket_labels)
            expected_old = (now - timedelta(days=40)).strftime("%B %Y")
            assert any(label.startswith(expected_old) for label in bucket_labels)

    asyncio.run(exercise())


def test_large_result_set_rebuilds(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_many(config, 10000)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            tree = app.query_one("#tree")
            app.rebuild()
            await pilot.pause()
            # All 10000 emails present under the single date bucket, bodies not preloaded
            category_node = next(c for c in tree.root.children if c.children)
            assert len(category_node.children[0].children) == 10000

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
