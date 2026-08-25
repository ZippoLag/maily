from __future__ import annotations

from .db import Database


def grouped_rows(rows, categories, sort_field="last_received_at"):
    grouped = {category: [] for category in categories}
    for row in rows:
        grouped.setdefault(row["category"], []).append(row)
    for items in grouped.values():
        items.sort(key=lambda row: (row[sort_field] or ""), reverse=sort_field in ("first_received_at", "last_received_at", "importance"))
    return grouped


def run_tui(config, as_json: bool = False) -> int:
    try:
        from textual.app import App, ComposeResult
        from textual.widgets import Footer, Header, Static, Tree
    except ImportError as exc:
        raise RuntimeError("Install maily with the 'tui' extra to use the TUI") from exc

    class BrowseApp(App):
        BINDINGS = [("q", "quit", "Quit"), ("s", "sort", "Sort")]

        def __init__(self):
            super().__init__()
            self.sort_field = "last_received_at"
            self.sort_fields = ["first_received_at", "last_received_at", "importance", "sender_name", "sender_domain"]
            self.database = Database(config.database_file)
            self.status = Static("Read-only browsing")

        def on_mount(self) -> None:
            self.rebuild()

        def rebuild(self) -> None:
            tree = self.query_one(Tree)
            tree.clear()
            rows = self.database.categorized_messages()
            grouped = grouped_rows(rows, config.categories, self.sort_field)
            for category, items in grouped.items():
                category_node = tree.root.add(f"{category} ({len(items)})")
                for item in items:
                    label = item["subject"] or "(no subject)"
                    category_node.add(f"{item['sender_name'] or item['sender_email']}: {label}", data=dict(item))
            tree.root.expand()

        def action_sort(self) -> None:
            self.sort_field = self.sort_fields[(self.sort_fields.index(self.sort_field) + 1) % len(self.sort_fields)]
            self.status.update(f"Read-only browsing | sorted by {self.sort_field}")
            self.rebuild()

        def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
            if event.node.data:
                item = event.node.data
                self.status.update(f"{item['sender_email']} | {item['subject']} | {item['received_at']}")

        def on_unmount(self) -> None:
            self.database.close()

        def compose(self) -> ComposeResult:
            yield Header()
            root = Tree("Today's unread mail")
            yield root
            yield self.status
            yield Static("Read-only browsing. Run maily scan to refresh data.")
            yield Footer()

    BrowseApp().run()
    return 0