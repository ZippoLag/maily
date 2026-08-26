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
        from textual.containers import Vertical
        from textual.widgets import ModalScreen
    except ImportError as exc:
        raise RuntimeError("Install maily with the 'tui' extra to use the TUI") from exc

    class SummaryModal(ModalScreen):
        """Modal screen to display email summary."""
        
        def __init__(self, summary_text: str):
            super().__init__()
            self.summary_text = summary_text
        
        def compose(self) -> ComposeResult:
            yield Vertical(
                Static("Email Summary", classes="modal-title"),
                Static(self.summary_text, classes="modal-content"),
                Static("Press Escape to close", classes="modal-hint"),
            )

    class BrowseApp(App):
        BINDINGS = [("q", "quit", "Quit"), ("s", "sort", "Sort"), ("S", "summarize", "Summarize")]

        def __init__(self):
            super().__init__()
            self.sort_field = "last_received_at"
            self.sort_fields = ["first_received_at", "last_received_at", "importance", "sender_name", "sender_domain"]
            self.database = Database(config.database_file)
            self.status = Static("Read-only browsing")
            self.selected_email = None

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
                    self._add_email_node(category_node, item)
            tree.root.expand()

        def _add_email_node(self, parent_node, item):
            """Add an email node that can be expanded to show sender and body."""
            subject = item.get("subject") or "(no subject)"
            sender_name = item.get("sender_name") or ""
            sender_email = item.get("sender_email") or ""
            
            sender_label = sender_name if sender_name else sender_email
            email_node = parent_node.add(
                f"{sender_label}: {subject}",
                data=dict(item)
            )
            
            body = item.get("body", "") or "(no body)"
            if isinstance(body, str):
                body = body.replace('\n', ' ')[:1000]
            sender_display = f"From: {sender_name or '(unknown)'} <{sender_email}>"
            
            email_node.add(f"[dim]{sender_display}[/dim]")
            email_node.add(f"{body}")
            
            email_node.allow_expand = True

        def action_sort(self) -> None:
            self.sort_field = self.sort_fields[(self.sort_fields.index(self.sort_field) + 1) % len(self.sort_fields)]
            self.status.update(f"Read-only browsing | sorted by {self.sort_field}")
            self.rebuild()

        def action_summarize(self) -> None:
            """Generate and display summary for selected email."""
            if self.selected_email:
                summary = self._generate_summary(self.selected_email)
                self.push_screen(SummaryModal(summary))
            else:
                self.status.update("Select an email first to summarize")

        def _generate_summary(self, email_data):
            """Generate summary for an email using inference or deterministic fallback."""
            message_id = email_data.get("id", "")
            body = email_data.get("body", "") or ""
            sender_name = email_data.get("sender_name", "") or ""
            sender_email = email_data.get("sender_email", "") or ""
            subject = email_data.get("subject", "") or ""
            
            if not body:
                return "(no body to summarize)"
            
            fingerprint = hash(f"{message_id}:{body}")
            
            cached = self.database.get_summary(message_id, str(fingerprint))
            if cached:
                return cached
            
            summary_prompt = f"""Summarize this email in 2-3 sentences. Focus on action items, key information, and sender intent.

Email:
- From: {sender_name} <{sender_email}>
- Subject: {subject}
- Body: {body[:2000]}

Summary:"""
            
            try:
                from .ollama import OllamaProvider
                provider = OllamaProvider(config.ollama_url, config.ollama_model, config.ollama_timeout_seconds)
                if config.inference_enabled:
                    summary = provider.generate(summary_prompt)
                    self.database.store_summary(message_id, summary, config.ollama_model, str(fingerprint))
                    return summary
            except (ImportError, Exception):
                pass
            
            if len(body) <= 200:
                summary = f"Preview: {body[:200]}"
            else:
                summary = f"Preview: {body[:200]}... (truncated)"
            
            self.database.store_summary(message_id, summary, "", str(fingerprint))
            return summary

        def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
            if event.node.data:
                item = event.node.data
                self.status.update(f"{item['sender_email']} | {item['subject']} | {item['received_at']}")
                self.selected_email = item
            else:
                self.selected_email = None

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