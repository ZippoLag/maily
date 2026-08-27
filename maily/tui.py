from __future__ import annotations

# Lazy Textual import: raises a friendly error when the 'tui' extra is
# missing. Module-level so the app classes are importable for testing;
# cli.py imports this module only inside the `tui` command branch.
try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Checkbox, Footer, Header, Static, Tree
except ImportError as exc:
    raise RuntimeError("Install maily with the 'tui' extra to use the TUI") from exc

from typing import ClassVar

from .db import Database
from .learning import accept_suggestion, reject_suggestion


def grouped_rows(rows, categories, sort_field="last_received_at"):
    grouped = {category: [] for category in categories}
    for row in rows:
        grouped.setdefault(row["category"], []).append(row)
    for items in grouped.values():
        items.sort(
            key=lambda row: row[sort_field] or "",
            reverse=sort_field
            in ("first_received_at", "last_received_at", "importance"),
        )
    return grouped


def toggle_category(categories: list[str], category: str) -> list[str]:
    """Return categories with the given category added or removed."""
    if category in categories:
        return [c for c in categories if c != category]
    return [*categories, category]


def format_category_badges(categories: list[str], max_badges: int = 2) -> str:
    """Format secondary categories as a compact badge suffix."""
    if not categories:
        return ""
    visible = categories[:max_badges]
    label = ", ".join(visible)
    if len(categories) > max_badges:
        label += f" +{len(categories) - max_badges} more"
    return f" [{label}]"


def format_full_category_list(item: dict) -> str:
    """Full, untruncated category list for an email row (tooltip/status)."""
    categories = item.get("categories") or [item.get("category")]
    return ", ".join(categories)


def suggestion_list_text(suggestions) -> str:
    """Render pending rule suggestions as a numbered list."""
    if not suggestions:
        return "No pending suggestions."
    return "\n".join(
        f"{i + 1}. [{suggestion['category']}] {suggestion['pattern']}"
        for i, suggestion in enumerate(suggestions)
    )


def save_category_overrides(
    database: Database, message_ids: list[str], categories: list[str]
) -> None:
    """Persist category overrides for multiple messages; empty list clears the override."""
    for message_id in message_ids:
        if categories:
            database.set_user_override(message_id, categories)
        else:
            database.delete_user_override(message_id)


def email_pane_text(item: dict, width: int = 80) -> str:
    """Compose sender/subject/body text for the reading pane, wrapping to *width*.

    Preserves stored paragraph breaks.  Returns '(no body)' when the body is
    empty or missing.
    """
    import textwrap

    sender_name = item.get("sender_name") or ""
    sender_email = item.get("sender_email") or ""
    subject = item.get("subject") or "(no subject)"
    body = item.get("body") or ""

    header = f"From: {sender_name} <{sender_email}>\nSubject: {subject}"

    if not body:
        return f"{header}\n\n(no body)"

    # Wrap each paragraph independently, then rejoin with blank lines.
    paragraphs = body.split("\n")
    wrapped_parts: list[str] = []
    for para in paragraphs:
        if para.strip() == "":
            wrapped_parts.append("")  # preserve blank-line paragraph break
        else:
            wrapped_parts.append(textwrap.fill(para, width=width))
    wrapped_body = "\n".join(wrapped_parts)

    return f"{header}\n\n{wrapped_body}"


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


class SuggestionModal(ModalScreen):
    """Modal to review and confirm pending rule learning suggestions."""

    def __init__(self, suggestions, config_file, database):
        super().__init__()
        self.suggestions = list(suggestions)
        self.config_file = config_file
        self.database = database

    def compose(self) -> ComposeResult:
        self.content = Static(
            suggestion_list_text(self.suggestions), classes="modal-content"
        )
        yield Vertical(
            Static("Rule Suggestions", classes="modal-title"),
            self.content,
            Static("'a' accept | 'r' reject | Escape close", classes="modal-hint"),
        )

    def _refresh(self) -> None:
        self.content.update(suggestion_list_text(self.suggestions))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key in ("a", "r") and self.suggestions:
            suggestion = self.suggestions[0]
            if event.key == "a":
                accept_suggestion(self.database, self.config_file, suggestion["id"])
                self.app.notify(
                    f"Accepted: {suggestion['pattern']}", title="Suggestions"
                )
            else:
                reject_suggestion(self.database, suggestion["id"])
                self.app.notify(
                    f"Rejected: {suggestion['pattern']}", title="Suggestions"
                )
            self.suggestions = [
                s for s in self.suggestions if s["id"] != suggestion["id"]
            ]
            self._refresh()


class CategoryTree(Tree):
    """Tree that shows the full category list for the hovered email row."""

    def watch_hover_line(self, previous_hover_line: int, hover_line: int) -> None:
        if hover_line < 0:
            self.tooltip = None
            return
        node = self._get_node(hover_line)
        if node is not None and getattr(node, "data", None):
            self.tooltip = f"Categories: {format_full_category_list(node.data)}"
        else:
            self.tooltip = None


class CategoryEditModal(ModalScreen):
    """Modal screen to view and edit categories for selected emails."""

    def __init__(
        self, categories: list[str], initial: list[str], message_ids: list[str]
    ):
        super().__init__()
        self.categories = categories
        self.initial = initial
        self.message_ids = message_ids
        self.category_by_id = {
            f"cat-{i}": category for i, category in enumerate(categories)
        }

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Edit Categories", classes="modal-title"),
            *[
                Checkbox(category, value=category in self.initial, id=checkbox_id)
                for checkbox_id, category in self.category_by_id.items()
            ],
            Static(
                f"Editing {len(self.message_ids)} email(s). Press 's' to save, Escape to cancel.",
                classes="modal-hint",
            ),
        )

    def action_save(self) -> None:
        """Collect checked categories and dismiss with the result."""
        selected = [
            self.category_by_id[checkbox.id]
            for checkbox in self.query(Checkbox)
            if checkbox.value
        ]
        self.dismiss((self.message_ids, selected))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class BrowseApp(App):
    BINDINGS: ClassVar = [
        ("q", "quit", "Quit"),
        ("s", "sort", "Sort"),
        ("S", "summarize", "Summarize"),
        ("c", "edit_categories", "Edit categories"),
        ("m", "mark", "Mark/Unmark"),
        ("p", "suggestions", "Rule suggestions"),
    ]

    def __init__(self, config):
        super().__init__()
        self._config = config
        self.sort_field = "last_received_at"
        self.sort_fields = [
            "first_received_at",
            "last_received_at",
            "importance",
            "sender_name",
            "sender_domain",
        ]
        self.database = Database(config.database_file)
        self.status = Static("Read-only browsing")
        self.reading_pane = Static("Select an email to read.", id="reading-pane")
        self.selected_email = None
        self.selected_emails: list[dict] = []

    def on_mount(self) -> None:
        self.rebuild()

    def rebuild(self) -> None:
        tree = self.query_one(Tree)
        tree.clear()
        rows = self.database.categorized_messages()
        grouped = grouped_rows(rows, self._config.categories, self.sort_field)
        for category, items in grouped.items():
            category_node = tree.root.add(f"{category} ({len(items)})")
            for item in items:
                self._add_email_node(category_node, item)
        tree.root.expand()

    def _add_email_node(self, parent_node, item):
        """Add an email node that can be expanded to show sender and body."""
        from .models import primary_category

        subject = item.get("subject") or "(no subject)"
        sender_name = item.get("sender_name") or ""
        sender_email = item.get("sender_email") or ""

        sender_label = sender_name if sender_name else sender_email
        categories = item.get("categories") or [item.get("category")]
        primary = primary_category(categories)
        badge_suffix = (
            format_category_badges([c for c in categories if c != primary])
            if primary
            else ""
        )
        primary_prefix = f"[{primary}] " if primary else ""
        email_node = parent_node.add(
            f"{primary_prefix}{sender_label}: {subject}{badge_suffix}", data=dict(item)
        )

        email_node.allow_expand = True

    def action_sort(self) -> None:
        self.sort_field = self.sort_fields[
            (self.sort_fields.index(self.sort_field) + 1) % len(self.sort_fields)
        ]
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

        try:
            cached = self.database.get_summary(message_id, str(fingerprint))
            if cached:
                return cached
        except Exception:  # noqa: BLE001 - degrade on cache failure
            pass

        summary_prompt = f"""Summarize this email in 2-3 sentences. Focus on action items, key information, and sender intent.

Email:
- From: {sender_name} <{sender_email}>
- Subject: {subject}
- Body: {body[:2000]}

Summary:"""

        try:
            from .ollama import OllamaProvider

            provider = OllamaProvider(
                self._config.ollama_url,
                self._config.ollama_model,
                self._config.ollama_timeout_seconds,
            )
            if self._config.inference_enabled:
                summary = provider.generate(summary_prompt)
                try:
                    self.database.store_summary(
                        message_id, summary, self._config.ollama_model, str(fingerprint)
                    )
                except Exception:  # noqa: BLE001 - degrade on cache failure
                    pass
                return summary
        except (ImportError, Exception):
            pass

        if len(body) <= 200:
            summary = f"Preview: {body[:200]}"
        else:
            summary = f"Preview: {body[:200]}... (truncated)"

        try:
            self.database.store_summary(message_id, summary, "", str(fingerprint))
        except Exception:  # noqa: BLE001 - degrade on cache failure
            pass
        return summary

    def _update_reading_pane(self, item: dict) -> None:
        """Populate the reading pane with the selected email's content."""
        width = self.reading_pane.size.width or 80
        self.reading_pane.update(email_pane_text(item, width=width))

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if event.node.data:
            item = event.node.data
            self.status.update(
                f"{item['sender_email']} | {item['subject']} | Categories: {format_full_category_list(item)}"
            )
            self.selected_email = item
            self.selected_emails = [item]
            self._update_reading_pane(item)
        else:
            self.selected_email = None
            self.selected_emails = []
            self.reading_pane.update("Select an email to read.")

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Update focused email when the user navigates the tree."""
        if event.node.data:
            self.selected_email = event.node.data
            item = event.node.data
            categories_str = format_full_category_list(item)
            if self.selected_emails:
                self.status.update(
                    f"{len(self.selected_emails)} marked | "
                    f"{item['sender_email']} | {item['subject']} | Categories: {categories_str}"
                )
            else:
                self.status.update(
                    f"{item['sender_email']} | {item['subject']} | Categories: {categories_str}"
                )
            self._update_reading_pane(item)
        else:
            self.selected_email = None
            self.reading_pane.update("Select an email to read.")

    def action_suggestions(self) -> None:
        """Open the rule suggestion review modal."""
        suggestions = self.database.get_rule_suggestions(status="pending")
        self.push_screen(
            SuggestionModal(
                suggestions, self._config.home / "config.toml", self.database
            )
        )

    def action_mark(self) -> None:
        """Mark or unmark the selected email for batch category editing."""
        if not self.selected_email:
            self.status.update("Select an email first to mark")
            return
        item = self.selected_email
        if item in self.selected_emails:
            self.selected_emails.remove(item)
            self.status.update(
                f"Unmarked {item.get('subject')} ({len(self.selected_emails)} selected)"
            )
        else:
            self.selected_emails.append(item)
            self.status.update(
                f"Marked {item.get('subject')} ({len(self.selected_emails)} selected)"
            )

    def action_edit_categories(self) -> None:
        """Open the category edit modal for the selected email(s)."""
        if not self.selected_emails:
            self.status.update(
                "Select an email first (press 'c' on it, 'm' to mark more)"
            )
            return
        first = self.selected_emails[0]
        override = self.database.get_user_override(first["id"])
        if override is not None:
            initial = override
        else:
            initial = list(first.get("categories") or [first.get("category")])
        self._edit_initial = initial
        message_ids = [item["id"] for item in self.selected_emails]
        self.push_screen(
            CategoryEditModal(list(self._config.categories), initial, message_ids),
            self._on_categories_saved,
        )

    def _on_categories_saved(self, result) -> None:
        """Persist modal results, refresh the tree, and notify the user."""
        if result is None:
            return  # cancelled
        message_ids, categories = result
        initial = getattr(self, "_edit_initial", [])
        added = [c for c in categories if c not in initial]
        removed = [c for c in initial if c not in categories]
        save_category_overrides(self.database, message_ids, categories)
        self.rebuild()
        self.selected_emails = []
        self.selected_email = None
        if added:
            self.notify(f"Added: {', '.join(added)}", title="Categories")
        if removed:
            self.notify(f"Removed: {', '.join(removed)}", title="Categories")

    def on_unmount(self) -> None:
        self.database.close()

    def compose(self) -> ComposeResult:
        yield Header()
        root = CategoryTree("Today's unread mail")
        yield root
        yield self.reading_pane
        yield self.status
        yield Footer()


def run_tui(config, as_json: bool = False) -> int:
    BrowseApp(config).run()
    return 0
