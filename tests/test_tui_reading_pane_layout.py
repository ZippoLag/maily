"""Tests for tui-reading-pane-layout: fixed-height reading pane and toggle."""

import asyncio

from maily.config import load_config
from maily.tui import FIXED_PANE_HEIGHT, BrowseApp


def _long_body_item() -> dict:
    return {
        "id": "m1",
        "sender_name": "Alice",
        "sender_email": "alice@example.com",
        "subject": "A very long email",
        "body": ("word " * 800).strip(),  # way more than the pane can display
        "categories": ["Work"],
    }


def test_reading_pane_fixed_height_and_tree_expands(tmp_path):
    config = load_config(tmp_path / "home")

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test(size=(100, 50)):
            pane = app.query_one("#reading-pane")
            tree = app.query_one("#tree")

            # The reading pane has an explicit fixed height capped by
            # max_height so it can never grow past the bottom strip.
            assert pane.styles.height is not None
            assert int(pane.styles.max_height.value) == FIXED_PANE_HEIGHT

            # The email list takes the remaining space (fractional height).
            assert str(tree.styles.height).endswith("fr")

    asyncio.run(exercise())


def test_long_body_scrolls_within_fixed_pane(tmp_path):
    config = load_config(tmp_path / "home")

    async def exercise():
        app = BrowseApp(config)
        async with app.run_test(size=(100, 50)) as pilot:
            app._update_reading_pane(_long_body_item())
            await pilot.pause()
            pane = app.query_one("#reading-pane")

            # Long content does not grow the pane: it stays at its fixed height.
            assert pane.size.height == FIXED_PANE_HEIGHT
            # Vertical scrolling is enabled so the content scrolls internally.
            assert str(pane.styles.overflow_y).lower() in ("auto", "scroll")

    asyncio.run(exercise())
