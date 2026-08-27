import asyncio
from types import SimpleNamespace

from textual.widgets import ProgressBar

from maily.config import load_config
from maily.db import Database
from maily.tui import (
    BrowseApp,
    CategoryEditModal,
    DigestModal,
    SuggestionModal,
    SummaryModal,
)


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
            app.screen.on_key(SimpleNamespace(key="escape"))
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


def test_email_nodes_are_not_expandable(tmp_path):
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            tree = app.query_one("#tree")
            await pilot.pause()
            email_node = _first_email_node(tree)
            assert email_node is not None
            assert email_node.allow_expand is False
            # Expanding the node adds no children (no lazy body load / triangles).
            email_node.expand()
            await pilot.pause()
            assert len(email_node.children) == 0

    asyncio.run(exercise())


def test_email_row_line_format(tmp_path):
    from maily.tui import email_line_text

    # Single sender, unmarked -> [ ] sender subject
    assert (
        email_line_text({"subject": "Hello", "sender_email": "alice@example.com"})
        == "[ ] alice@example.com Hello"
    )
    # Multiple senders, marked -> [x] ... first subject
    assert (
        email_line_text(
            {
                "subject": "Update",
                "senders": ["a@x.com", "b@x.com"],
            },
            marked=True,
        )
        == "[x] ... a@x.com Update"
    )

    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            tree = app.query_one("#tree")
            await pilot.pause()
            # Mark the real tree node's data object (the node stores a dict) so
            # the row re-renders with the checkbox reflected via the helper.
            node = _first_email_node(tree)
            item = node.data
            app.on_tree_node_highlighted(
                SimpleNamespace(node=SimpleNamespace(data=item))
            )
            app.selected_emails = []
            app.action_mark()
            app.rebuild()
            await pilot.pause()
            marked_node = _first_email_node(tree)
            assert "[x]" in str(marked_node.label)
            assert "[ ]" not in str(marked_node.label)

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


def test_digest_hotkey_opens_modal_and_dismisses(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_many(config, 3)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            assert ("d", "digest", "Digest view") in app.BINDINGS
            app.action_digest()
            await pilot.pause()
            assert isinstance(app.screen, DigestModal)
            assert "3 emails" in str(app.screen.digest_text)
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()
            assert not isinstance(app.screen, DigestModal)

    asyncio.run(exercise())


def test_digest_cached_for_same_view(tmp_path, monkeypatch):
    config = load_config(tmp_path / "home")
    _seed_many(config, 3)
    calls = []

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()

            def fake_generate_digest(items, infer=None, model=""):
                calls.append(1)
                return "digest-text", "deterministic"

            monkeypatch.setattr("maily.tui.generate_digest", fake_generate_digest)
            app.action_digest()
            await pilot.pause()
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()
            app.action_digest()
            await pilot.pause()
            assert isinstance(app.screen, DigestModal)
            # Same view: second digest served from cache, generator not re-run
            assert len(calls) == 1
            assert app.screen.cached is True

    asyncio.run(exercise())


def test_digest_view_change_generates_new_digest(tmp_path, monkeypatch):
    config = load_config(tmp_path / "home")
    _seed_many(config, 3)
    calls = []

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()

            def fake_generate_digest(items, infer=None, model=""):
                calls.append(sorted(item["id"] for item in items))
                return f"digest-{len(calls)}", "deterministic"

            monkeypatch.setattr("maily.tui.generate_digest", fake_generate_digest)
            app.action_digest()
            await pilot.pause()
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()
            # A different set of visible emails means a different view.
            app._visible_email_nodes = lambda tree: [{"id": "m0"}, {"id": "m1"}]
            app.action_digest()
            await pilot.pause()
            assert len(calls) == 2
            assert app.screen.cached is False

    asyncio.run(exercise())


def test_digest_uses_inference_when_enabled(tmp_path, monkeypatch):
    from dataclasses import replace

    config = load_config(tmp_path / "home")
    _seed_many(config, 2)
    config = replace(config, inference_enabled=True)

    class FakeProvider:
        def generate(self, prompt):
            return "AI-generated digest"

    monkeypatch.setattr("maily.ollama.OllamaProvider", lambda *a, **k: FakeProvider())

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_digest()
            await pilot.pause()
            assert isinstance(app.screen, DigestModal)
            assert "AI-generated digest" in str(app.screen.digest_text)

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


def test_summary_modal_dismisses_on_escape(tmp_path):
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            app.on_tree_node_selected(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            app.action_summarize()
            await pilot.pause()
            assert isinstance(app.screen, SummaryModal)
            # Escape key closes the modal.
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()
            assert not isinstance(app.screen, SummaryModal)

    asyncio.run(exercise())


def test_digest_modal_dismisses_on_escape(tmp_path):
    config = load_config(tmp_path / "home")
    _seed_many(config, 3)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_digest()
            await pilot.pause()
            assert isinstance(app.screen, DigestModal)
            # Escape key closes the modal.
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()
            assert not isinstance(app.screen, DigestModal)

    asyncio.run(exercise())


def test_suggestion_modal_dismisses_on_escape(tmp_path):
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_suggestions()
            await pilot.pause()
            assert isinstance(app.screen, SuggestionModal)
            # Escape key closes the modal.
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()
            assert not isinstance(app.screen, SuggestionModal)

    asyncio.run(exercise())


def test_resolve_target_emails_fallback_branches(tmp_path):
    """Shared resolve helper: marked set wins, else selected, else none."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            marked = [{"id": "m1", "subject": "One"}, {"id": "m2", "subject": "Two"}]
            selected = {"id": "m9", "subject": "Sel"}
            # Marked set wins over the selected email.
            app.selected_emails = marked
            app.selected_email = selected
            assert app._resolve_target_emails() == marked
            # No marks -> the single selected email.
            app.selected_emails = []
            assert app._resolve_target_emails() == [selected]
            # No marks and no selection -> empty.
            app.selected_email = None
            assert app._resolve_target_emails() == []

    asyncio.run(exercise())


def test_edit_categories_marked_selected_none(tmp_path):
    """c applies to marked then selected emails and no-ops without a target."""
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            await pilot.pause()
            # No target: no-op, no modal opens.
            app.selected_email = None
            app.selected_emails = []
            app.action_edit_categories()
            await pilot.pause()
            assert not isinstance(app.screen, CategoryEditModal)
            # Only a selection -> opens modal targeting that email.
            app.selected_email = _item()
            app.action_edit_categories()
            await pilot.pause()
            assert isinstance(app.screen, CategoryEditModal)
            assert "m1" in app.screen.message_ids
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()
            # Marked emails take precedence when both are present.
            app.selected_emails = [{**_item(), "id": "m2", "subject": "Two"}]
            app.action_edit_categories()
            await pilot.pause()
            assert isinstance(app.screen, CategoryEditModal)
            assert app.screen.message_ids == ["m2"]
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()

    asyncio.run(exercise())


def test_category_edit_modal_dismisses_on_escape(tmp_path):
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            app.on_tree_node_selected(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            app.action_edit_categories()
            await pilot.pause()
            assert isinstance(app.screen, CategoryEditModal)
            # Escape key closes the modal without saving.
            app.screen.on_key(SimpleNamespace(key="escape"))
            await pilot.pause()
            assert not isinstance(app.screen, CategoryEditModal)

    asyncio.run(exercise())


def test_category_edit_modal_saves_on_s(tmp_path):
    config = load_config(tmp_path / "home")
    _seed(config)

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test() as pilot:
            app.on_tree_node_selected(
                SimpleNamespace(node=SimpleNamespace(data=_item()))
            )
            app.action_edit_categories()
            await pilot.pause()
            assert isinstance(app.screen, CategoryEditModal)
            # 's' key saves and closes the modal.
            app.screen.action_save()
            await pilot.pause()
            assert not isinstance(app.screen, CategoryEditModal)

    asyncio.run(exercise())
