from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import ClassVar

# Lazy Textual import: raises a friendly error when the 'tui' extra is
# missing. Module-level so the app classes are importable for testing;
# cli.py imports this module only inside the `tui` command branch.
try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Checkbox, Footer, Header, ProgressBar, Static, Tree
except ImportError as exc:
    raise RuntimeError("Install maily with the 'tui' extra to use the TUI") from exc

from .db import Database
from .learning import accept_suggestion, reject_suggestion

THEME_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "invoice",
        re.compile(r"\binvoice\b|\bpayment\b|\bbill\b|\breceipt\b", re.IGNORECASE),
    ),
    ("newsletter", re.compile(r"\bunsubscribe\b|\bnewsletter\b", re.IGNORECASE)),
    (
        "meeting request",
        re.compile(r"\bmeeting\b|\binvite\b|\bcalendar\b|\bschedule\b", re.IGNORECASE),
    ),
    (
        "verification code",
        re.compile(r"\bverification\b|\bcode\b|\bOTP\b|\b2FA\b", re.IGNORECASE),
    ),
    (
        "job alert",
        re.compile(
            r"\bjob\b|\bhiring\b|\bvacancy\b|\brecruit\b|\bcareer\b", re.IGNORECASE
        ),
    ),
)


def count_themes(items: list[dict]) -> str:
    """Count common themes across items, rendered as '3 invoices, 2 meetings'."""
    counts: Counter[str] = Counter()
    for item in items:
        text = f"{item.get('subject', '')} {item.get('body', '')}"
        for label, pattern in THEME_PATTERNS:
            if pattern.search(text):
                counts[label] += 1
    if not counts:
        return ""
    return ", ".join(f"{n} {label}s" for label, n in counts.most_common())


def generate_digest(items: list[dict], infer=None, model: str = "") -> tuple[str, str]:
    """Build a digest of the given emails.

    Returns ``(digest_text, source)`` where source is ``"inference"`` when an
    inference callable produced the digest and ``"deterministic"`` otherwise.
    """
    count = len(items)
    counts: dict[str, int] = {}
    for item in items:
        for category in item.get("categories") or [item.get("category")]:
            counts[category] = counts.get(category, 0) + 1
    breakdown = ", ".join(f"{n} {cat}" for cat, n in counts.items())
    header = f"{count} email{'s' if count != 1 else ''}: {breakdown or 'no categories'}"
    if infer is not None:
        try:
            listing = "\n".join(
                f"- [{item.get('category', '')}] {item.get('sender_email', '')}: "
                f"{item.get('subject', '')} - {item.get('body', '')[:200]}"
                for item in items[:50]
            )
            prompt = (
                "Summarize the key themes and action items across these emails "
                f"({count} total, showing first {min(count, 50)}):\n{listing}"
            )
            return infer(prompt), "inference"
        except Exception:  # noqa: BLE001, S110 - degrade to deterministic digest
            pass
    themes = count_themes(items)
    themes_line = f"Themes: {themes}" if themes else "Themes: none detected"
    return f"{header}\n{themes_line}", "deterministic"


def date_group_label(received_at: str, now: datetime | None = None) -> str:
    """Bucket an ISO received_at into a human date group (Today/Yesterday/Last Week/Month Year)."""
    parsed = datetime.fromisoformat(received_at)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    current = now or datetime.now(UTC)
    today = current.date()
    day = parsed.date()
    if day == today:
        return "Today"
    if day == today - timedelta(days=1):
        return "Yesterday"
    if day > today - timedelta(days=7):
        return "Last Week"
    return parsed.strftime("%B %Y")


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


def email_line_text(item: dict, marked: bool = False) -> str:
    """Render a single email list row: `[ ]`/`[x]` mark, sender summary, subject.

    The sender summary is the first sender address, prefixed with ``... `` when
    the message has more than one sender. Returns plain text (no Rich markup);
    callers add label badge markup separately.
    """
    subject = item.get("subject") or "(no subject)"
    senders = item.get("senders") or ()
    first_sender = ""
    if senders:
        first_sender = str(senders[0])
    else:
        first_sender = item.get("sender_email") or item.get("sender_name") or ""
    if len(senders) > 1:
        sender_summary = f"... {first_sender}"
    else:
        sender_summary = first_sender
    return f"{mark_prefix(marked)}{sender_summary} {subject}".rstrip()


def mark_prefix(marked: bool) -> str:
    """Return the checkbox prefix for a row's mark state."""
    return "[x] " if marked else "[ ] "


def html_to_readable(body: str) -> str:
    """Convert an HTML email body to readable Markdown/plain text.

    Plain-text bodies pass through unchanged. HTML bodies are converted with
    ``html2text``; if the converter is unavailable or conversion fails, the
    original body is returned so the TUI keeps working and never shows raw
    markup.
    """
    # Only attempt conversion when the body looks like HTML (contains tags).
    if "<" not in body:
        return body
    try:
        import html2text

        return html2text.html2text(body)
    except Exception:  # noqa: BLE001 - fall back on any conversion error
        return body


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

    # Convert HTML bodies to clean Markdown/plain text before wrapping.
    body = html_to_readable(body)

    # Wrap each paragraph independently, then rejoin with blank lines.
    paragraphs = body.split("\n")
    wrapped_parts: list[str] = []
    for para in paragraphs:
        if para.strip() == "":
            wrapped_parts.append("")
        else:
            wrapped_parts.append(textwrap.fill(para, width=width))
    wrapped_body = "\n".join(wrapped_parts)

    return f"{header}\n\n{wrapped_body}"


_LABEL_COLORS = ("red", "green", "blue", "magenta", "cyan", "yellow")


def format_label_badges(labels, max_badges: int = 2) -> str:
    """Render user labels as colored inline badges, truncating with '+N more'.

    Labels are styled with a deterministic color per label so badges stay
    distinguishable at a glance.
    """
    labels = list(labels or ())
    if not labels:
        return ""
    shown = labels[:max_badges]
    parts = []
    for label in shown:
        color = _LABEL_COLORS[hash(label) % len(_LABEL_COLORS)]
        parts.append(f"[{color}]{label}[/]")
    if len(labels) > max_badges:
        parts.append(f"[dim]+{len(labels) - max_badges} more[/]")
    return " " + " ".join(parts)


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

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class DigestModal(ModalScreen):
    """Modal screen showing a digest of the currently visible emails."""

    def __init__(self, digest_text: str, cached: bool = False):
        super().__init__()
        self.digest_text = digest_text
        self.cached = cached

    def compose(self) -> ComposeResult:
        title = "View Digest" + (" (cached)" if self.cached else "")
        yield Vertical(
            Static(title, classes="modal-title"),
            Static(self.digest_text, classes="modal-content"),
            Static("Press Escape to close", classes="modal-hint"),
        )

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


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
        if node is None:
            self.tooltip = None
            return
        data = node.data
        if data is not None:
            self.tooltip = f"Categories: {format_full_category_list(data)}"
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
        self.confirming = False
        self.category_by_id = {
            f"cat-{i}": category for i, category in enumerate(categories)
        }

    def _collected(self) -> list[str]:
        return [
            self.category_by_id[checkbox.id]
            for checkbox in self.query(Checkbox)
            if checkbox.value and checkbox.id is not None
        ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Edit Categories", classes="modal-title"),
            *[
                Checkbox(category, value=category in self.initial, id=checkbox_id)
                for checkbox_id, category in self.category_by_id.items()
            ],
            Static(
                f"Editing {len(self.message_ids)} email(s). Press 's' to save, Escape to cancel.",
                id="edit-hint",
                classes="modal-hint",
            ),
        )

    def action_save(self) -> None:
        """Collect checked categories; confirm before applying to multiple emails."""
        selected = self._collected()
        if len(self.message_ids) > 1 and not self.confirming:
            self.confirming = True
            hint = self.query_one("#edit-hint", Static)
            hint.update(
                f"Apply to {len(self.message_ids)} emails? Press 'y' to confirm, 'n' to cancel."
            )
            return
        self.dismiss((self.message_ids, selected))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            return
        if self.confirming:
            if event.key == "y":
                self.dismiss((self.message_ids, self._collected()))
            elif event.key == "n":
                self.dismiss(None)


class IntentsModal(ModalScreen):
    """Modal listing pending mutation intents."""

    def __init__(self, lines, app):
        super().__init__()
        self.lines = lines
        self.app = app

    def compose(self) -> ComposeResult:
        yield Vertical(*self.lines)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


def _confidence_label(confidence: float) -> str:
    """Render a confidence score as a colored label (High/Medium/Low)."""
    if confidence >= 0.8:
        return f"[green]High ({confidence:.0%})[/]"
    if confidence >= 0.5:
        return f"[yellow]Medium ({confidence:.0%})[/]"
    return f"[gray]Low ({confidence:.0%})[/]"


class BatchSuggestionsModal(ModalScreen):
    """Modal listing batch action suggestions for the current selection."""

    app: BrowseApp

    def __init__(
        self, suggestions, selected_emails, app, filter_type: str | None = None
    ):
        super().__init__()
        self.suggestions = suggestions
        self.selected_emails = selected_emails
        self.app = app
        self.filter_type = filter_type
        self.undo_snapshot: dict[str, list[str] | None] = {}

    def _visible(self) -> list:
        if not self.filter_type:
            return self.suggestions
        return [s for s in self.suggestions if s.action == self.filter_type]

    def compose(self) -> ComposeResult:
        visible = self._visible()
        lines = [
            Static("Batch Action Suggestions", classes="modal-title"),
            Static(
                f"{len(self.selected_emails)} email(s) selected."
                + (f"  (filtered: {self.filter_type})" if self.filter_type else ""),
                classes="modal-hint",
            ),
        ]
        if not visible:
            lines.append(Static("No suggestions for this selection."))
        for index, suggestion in enumerate(visible):
            label = suggestion.description
            count = len(suggestion.email_ids or ())
            affected = f" ({count} emails)" if count else ""
            if suggestion.requires_write:
                label += "  (read-only: queued as intent)"
            lines.append(
                Static(
                    f"{index + 1}. {label}{affected} — "
                    f"{_confidence_label(suggestion.confidence)}",
                    classes="modal-content",
                )
            )
        lines.append(
            Static(
                "Number: apply categorize / queue mutation · f: filter · a: accept all "
                "· Escape: close",
                classes="modal-hint",
            )
        )
        yield Vertical(*lines)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            return
        visible = self._visible()
        if event.key == "f":
            order = [None, "categorize", "archive", "delete", "mark-read"]
            current = order.index(self.filter_type) if self.filter_type in order else 0
            self.filter_type = order[(current + 1) % len(order)]
            self.refresh(recompose=True)
            return
        if event.key == "a":
            for suggestion in visible:
                if (
                    not suggestion.requires_write
                    and suggestion.action == "categorize"
                    and suggestion.category
                ):
                    self.app._apply_batch_categorization(
                        suggestion, list(suggestion.email_ids)
                    )
            self.dismiss(None)
            return
        if event.key.isdigit() and event.key != "0":
            index = int(event.key) - 1
            if 0 <= index < len(visible):
                suggestion = visible[index]
                if suggestion.requires_write:
                    self.app._queue_mutation_intent(suggestion)
                    return
                if suggestion.action == "categorize" and suggestion.category:
                    self.dismiss((suggestion, list(suggestion.email_ids)))

    def on_mount(self) -> None:
        self.focus()


FIXED_PANE_HEIGHT = 10  # reading pane bottom strip height in lines


class BrowseApp(App):
    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("q", "quit", "Quit"),
        ("s", "sort", "Sort"),
        ("S", "summarize", "Summarize"),
        ("c", "edit_categories", "Edit categories"),
        ("p", "suggestions", "Rule suggestions"),
        ("d", "digest", "Digest view"),
        ("space", "mark", "Mark/Unmark"),
        ("enter", "mark", "Mark/Unmark"),
        ("ctrl+m", "mark_all_date", "Mark/Unmark all today"),
        ("escape", "clear_selection", "Clearing marks"),
        ("l", "filter_by_label", "Filter by label"),
        ("b", "batch_suggestions", "Batch suggestions"),
        ("u", "undo_batch", "Undo last batch"),
        ("i", "view_intents", "View pending intents"),
        ("pageup", "page_up", "Page Up"),
        ("pagedown", "page_down", "Page Down"),
        ("home", "home", "Home"),
        ("end", "end", "End"),
    ]

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.sort_field = "last_received_at"
        self.sort_fields = [
            "first_received_at",
            "last_received_at",
            "importance",
            "sender_name",
            "sender_domain",
        ]
        self.database = Database(
            config.database_file, body_cache_size=config.performance_body_cache_size
        )
        self.status = Static("Read-only browsing")
        self.reading_pane = Static("Select an email to read.", id="reading-pane")
        self.selected_email = None
        self.selected_emails: list[dict] = []
        self.email_count = 0
        self._label_filter: str | None = None
        self._digest_cache: dict[tuple, str] = {}
        self._suggestion_cache: dict[tuple, list] = {}
        self._batch_undo_snapshot: tuple[list[str], list[list[str] | None]] | None = (
            None
        )

    def on_mount(self) -> None:
        self.rebuild()

    def rebuild(self) -> None:
        tree = self.query_one(Tree)
        tree.clear()
        rows = self.database.categorized_messages()
        if self._label_filter:
            rows = [
                row for row in rows if self._label_filter in (row.get("labels") or ())
            ]
        grouped = grouped_rows(rows, self.config.categories, self.sort_field)
        total_emails = sum(len(items) for items in grouped.values())
        self.email_count = total_emails
        tree.root.label = f"{total_emails} emails"
        self.status.update(f"Read-only browsing | {total_emails} emails")
        progress = self.query_one("#load-progress", ProgressBar)
        progress.display = True
        progress.total = len(grouped)
        progress.progress = 0
        for index, (category, items) in enumerate(grouped.items()):
            category_node = tree.root.add(f"{category} ({len(items)})")
            buckets: dict[str, list[dict]] = {}
            for item in items:
                buckets.setdefault(date_group_label(item["received_at"]), []).append(
                    item
                )
            for bucket, bucket_items in buckets.items():
                bucket_node = category_node.add(f"{bucket} ({len(bucket_items)})")
                for item in bucket_items:
                    self._add_email_node(bucket_node, item)
            progress.progress = index + 1
        tree.root.expand()
        self._expand_group_nodes(tree.root)
        progress.display = False

    def _expand_group_nodes(self, node) -> None:
        """Expand category and date-bucket nodes so emails are visible.

        Email nodes (which carry item data) are not expandable; the reading
        pane shows a highlighted email's details.
        """
        for child in node.children:
            if child.data is None:
                child.expand()
                self._expand_group_nodes(child)

    def _add_email_node(self, parent_node, item):
        """Add a non-expandable email node using the standard line format."""
        from rich.markup import escape

        is_marked = item in self.selected_emails
        plain = escape(email_line_text(item, marked=is_marked))
        badge_markup = format_label_badges(item.get("labels"))
        email_node = parent_node.add(f"{plain}{badge_markup}", data=dict(item))
        email_node.allow_expand = False

    def action_sort(self) -> None:
        self.sort_field = self.sort_fields[
            (self.sort_fields.index(self.sort_field) + 1) % len(self.sort_fields)
        ]
        self.notify(f"Sorted by {self.sort_field}", title="Sort", timeout=3)
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
        except Exception:  # noqa: BLE001, S110 - degrade on cache failure
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
                self.config.ollama_url,
                self.config.ollama_model,
                self.config.ollama_timeout_seconds,
            )
            if self.config.inference_enabled:
                summary = provider.generate(summary_prompt)
                try:
                    self.database.store_summary(
                        message_id, summary, self.config.ollama_model, str(fingerprint)
                    )
                except Exception:  # noqa: BLE001, S110 - degrade on cache failure
                    pass
                return summary
        except Exception:  # noqa: BLE001, S110 - degraded fallback when inference is unavailable
            pass

        if len(body) <= 200:
            summary = f"Preview: {body[:200]}"
        else:
            summary = f"Preview: {body[:200]}... (truncated)"

        try:
            self.database.store_summary(message_id, summary, "", str(fingerprint))
        except Exception:  # noqa: BLE001, S110 - degrade on cache failure
            pass
        return summary

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

    def _update_reading_pane(self, item: dict) -> None:
        """Populate the reading pane with the selected email's content."""
        width = self.reading_pane.size.width or 80
        self.reading_pane.update(email_pane_text(item, width=width))

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

    def _visible_email_nodes(self, tree):
        """Return the email rows currently visible in the tree viewport."""
        start = max(0, tree.scroll_offset.y)
        end = start + tree.size.height
        nodes = []
        for line in range(start, end):
            node = tree._get_node(line)
            if node is not None and node.data is not None:
                nodes.append(node.data)
        return nodes

    def action_digest(self) -> None:
        """Generate and display a digest of the currently visible emails."""
        tree = self.query_one(Tree)
        nodes = self._visible_email_nodes(tree)
        if not nodes:
            self.status.update("No emails visible to digest")
            return
        view_key = (self.sort_field, tuple(sorted(node["id"] for node in nodes)))
        cached_text = self._digest_cache.get(view_key)
        if cached_text is not None:
            self.push_screen(DigestModal(cached_text, cached=True))
            return
        infer = None
        if self.config.inference_enabled:
            try:
                from .ollama import OllamaProvider

                provider = OllamaProvider(
                    self.config.ollama_url,
                    self.config.ollama_model,
                    self.config.ollama_timeout_seconds,
                )
                infer = provider.generate
            except Exception:  # noqa: BLE001, S110 - degraded fallback when inference is unavailable
                pass
        text, _ = generate_digest(nodes, infer=infer, model=self.config.ollama_model)
        self._digest_cache[view_key] = text
        self.push_screen(DigestModal(text))

    def action_page_up(self) -> None:
        self.query_one(Tree).scroll_page_up(animate=False)

    def action_page_down(self) -> None:
        self.query_one(Tree).scroll_page_down(animate=False)

    def action_home(self) -> None:
        self.query_one(Tree).scroll_home(animate=False)

    def action_end(self) -> None:
        self.query_one(Tree).scroll_end(animate=False)

    def action_deselect_all(self) -> None:
        """Clear the marked set."""
        self.selected_emails = []
        self.status.update("Cleared marks")
        self.rebuild()

    def action_clear_selection(self) -> None:
        """Escape clears the marked set when no modal is open."""
        self.action_deselect_all()

    def action_filter_by_label(self) -> None:
        """Toggle a label filter based on the focused email (press again to clear)."""
        if self._label_filter:
            self._label_filter = None
            self.status.update("Label filter cleared")
            self.rebuild()
            return
        if not self.selected_email:
            self.status.update("Select an email first to filter by label")
            return
        labels = list(self.selected_email.get("labels") or ())
        if not labels:
            self.status.update("Focused email has no user labels to filter by")
            return
        self._label_filter = labels[0]
        self.status.update(f"Filtered by label: {self._label_filter}")
        self.rebuild()

    def action_batch_suggestions(self) -> None:
        """Open batch action suggestions for the current selection ('b')."""
        if not self.selected_emails:
            self.status.update("Mark emails first (Space/Enter) for suggestions")
            return
        from .suggestions import cache_key, generate_suggestions

        key = cache_key(self.selected_emails)
        suggestions = self._suggestion_cache.get(key)
        if suggestions is None:
            infer = None
            if self.config.inference_enabled:
                try:
                    from .ollama import OllamaProvider

                    provider = OllamaProvider(
                        self.config.ollama_url,
                        self.config.ollama_model,
                        self.config.ollama_timeout_seconds,
                    )
                    infer = provider.generate
                except Exception:  # noqa: BLE001, S110 - fall back to deterministic
                    pass
            suggestions = generate_suggestions(
                list(self.selected_emails),
                infer=infer,
                confidence_threshold=self.config.suggestions_confidence_threshold,
            )
            self._suggestion_cache[key] = suggestions
        self.push_screen(
            BatchSuggestionsModal(suggestions, self.selected_emails, self),
            self._on_batch_suggestion,
        )

    def _on_batch_suggestion(self, result) -> None:
        """Apply an accepted categorize suggestion."""
        if result is None:
            return  # cancelled
        suggestion, message_ids = result
        if suggestion.action == "categorize":
            self._apply_batch_categorization(suggestion, message_ids)

    def _queue_mutation_intent(self, suggestion) -> None:
        """Queue an accepted mutation suggestion as a pending intent."""
        self.database.save_mutation_intent(
            action=suggestion.action,
            message_ids=list(suggestion.email_ids or ()),
            target=suggestion.target,
            description=suggestion.description,
        )
        self.notify(
            f"Queued '{suggestion.action}' for {len(suggestion.email_ids or ())} "
            "email(s) as a pending intent (needs Gmail write access)",
            title="Batch",
        )

    def action_view_intents(self) -> None:
        """Show pending mutation intents in a modal ('i')."""
        intents = self.database.list_mutation_intents()
        if not intents:
            self.status.update("No pending mutation intents")
            return
        lines = [Static("Pending Mutation Intents", classes="modal-title")]
        for intent in intents:
            lines.append(
                Static(
                    f"#{intent['id']} {intent['action']}: {intent['description']} "
                    f"({len(intent['message_ids'])} emails)",
                    classes="modal-content",
                )
            )
        lines.append(Static("Press Escape to close.", classes="modal-hint"))
        self.push_screen(IntentsModal(lines, self))

    def action_undo_batch(self) -> None:
        """Restore category overrides from before the last batch apply ('u')."""
        snapshot = getattr(self, "_batch_undo_snapshot", None)
        if not snapshot:
            self.status.update("Nothing to undo")
            return
        message_ids, previous = snapshot
        for message_id, previous_categories in zip(message_ids, previous):
            if previous_categories:
                self.database.set_user_override(message_id, previous_categories)
            else:
                self.database.delete_user_override(message_id)
        self._batch_undo_snapshot = None
        self.rebuild()
        self.notify(
            f"Undid batch categorization for {len(message_ids)} email(s)", title="Batch"
        )

    def _apply_batch_categorization(self, suggestion, message_ids: list[str]) -> None:
        """Apply a categorize suggestion to the target emails, reporting failures."""
        previous = [
            self.database.get_user_override(message_id) for message_id in message_ids
        ]
        failures: list[str] = []
        try:
            save_category_overrides(self.database, message_ids, [suggestion.category])
        except Exception as exc:  # noqa: BLE001 - surface partial failure
            failures.append(str(exc))
        for message_id in message_ids:
            self.database.record_action(
                message_id, "batch-categorize", {"category": suggestion.category}
            )
        self._batch_undo_snapshot = (list(message_ids), previous)
        self.rebuild()
        if failures:
            self.notify(f"Categorized with {len(failures)} failure(s)", title="Batch")
        else:
            self.notify(
                f"Categorized {len(message_ids)} email(s) as {suggestion.category}",
                title="Batch",
            )

    def action_suggestions(self) -> None:
        """Open the rule suggestion review modal."""
        suggestions = self.database.get_rule_suggestions(status="pending")
        self.push_screen(
            SuggestionModal(
                suggestions, self.config.home / "config.toml", self.database
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
                f"Unmarked {item.get('subject')} ({len(self.selected_emails)} marked)"
            )
        else:
            self.selected_emails.append(item)
            self.status.update(
                f"Marked {item.get('subject')} ({len(self.selected_emails)} marked)"
            )
        self.rebuild()

    def _resolve_target_emails(self) -> list[dict]:
        """Resolve the emails an action applies to: marked, else selected, else none.

        Returns the marked set when any email is marked; otherwise the single
        highlighted (selected) email; otherwise an empty list.
        """
        if self.selected_emails:
            return list(self.selected_emails)
        if self.selected_email:
            return [self.selected_email]
        return []

    def action_edit_categories(self) -> None:
        """Open the category edit modal for the marked, or selected, emails."""
        targets = self._resolve_target_emails()
        if not targets:
            self.status.update(
                "No email to edit: mark or select one first (Enter/Space)"
            )
            return
        first = targets[0]
        override = self.database.get_user_override(first["id"])
        if override is not None:
            initial = override
        else:
            initial = list(first.get("categories") or [first.get("category")])
        self._edit_initial = initial
        message_ids = [item["id"] for item in targets]
        self.push_screen(
            CategoryEditModal(list(self.config.categories), initial, message_ids),
            self._on_categories_saved,
        )

    def action_mark_all_date(self) -> None:
        """Toggle the mark state of every email received today (Ctrl+M).

        Uses the same "Today" date scope as the tree/digest. When any current
        date email is unmarked this marks them all; otherwise it unmarks them all.
        """
        rows = self.database.categorized_messages()
        today_items = [
            row for row in rows if date_group_label(row["received_at"]) == "Today"
        ]
        if not today_items:
            self.status.update("No emails today to mark")
            return
        all_marked = all(item in self.selected_emails for item in today_items)
        if all_marked:
            ids = {item["id"] for item in today_items}
            self.selected_emails = [
                item for item in self.selected_emails if item["id"] not in ids
            ]
            self.status.update(f"Unmarked all {len(today_items)} email(s) today")
        else:
            ids = {item["id"] for item in self.selected_emails}
            for item in today_items:
                if item["id"] not in ids:
                    self.selected_emails.append(item)
            self.status.update(f"Marked all {len(today_items)} email(s) today")
        self.rebuild()

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
        root = CategoryTree("Today's unread mail", id="tree")
        # The email list takes all space above the fixed-height reading pane.
        root.styles.height = "1fr"
        yield root
        # Fixed bottom strip: the reading pane never grows past this height.
        self.reading_pane.styles.height = FIXED_PANE_HEIGHT
        self.reading_pane.styles.max_height = FIXED_PANE_HEIGHT
        # Long bodies scroll inside the fixed strip instead of growing it.
        self.reading_pane.styles.overflow_y = "auto"
        yield self.reading_pane
        yield self.status
        yield ProgressBar(id="load-progress", show_eta=False, show_percentage=True)
        yield Static(
            "Read-only browsing. Run maily scan to refresh data. 'd' digests the visible emails."
        )
        yield Footer()


def run_tui(config, as_json: bool = False) -> int:
    BrowseApp(config).run()
    return 0
