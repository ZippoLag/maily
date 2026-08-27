"""Batch action suggestions for the TUI.

Analyzes a selection of emails and produces deterministic suggestions
(categorize / mark-read / archive / delete) with confidence scores.  Mutating
actions are always marked ``requires_write`` — the TUI may only apply
categorization locally; the rest are read-only suggestions for a future
mutation workflow.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

MUTATING_ACTIONS = ("mark-read", "archive", "delete")


@dataclass(frozen=True)
class Suggestion:
    action: str
    target: str
    description: str
    confidence: float
    category: str | None = None
    requires_write: bool = False
    email_ids: tuple[str, ...] = field(default_factory=tuple)


def analyze_batch(emails: list[dict]) -> dict[str, Counter]:
    """Summarize a selection by sender, domain, and label."""
    senders: Counter[str] = Counter()
    domains: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    for email in emails:
        sender = (email.get("sender_name") or email.get("sender_email") or "").strip()
        if sender:
            senders[sender] += 1
        domain = (email.get("sender_domain") or "").strip()
        if domain:
            domains[domain] += 1
        for label in email.get("labels") or ():
            labels[label] += 1
        for category in email.get("categories") or (
            [email["category"]] if email.get("category") else []
        ):
            categories[category] += 1
    return {
        "senders": senders,
        "domains": domains,
        "labels": labels,
        "categories": categories,
    }


def _confidence(count: int, total: int) -> float:
    """Heuristic confidence: larger, more consistent groups score higher."""
    if total == 0:
        return 0.0
    ratio = count / total
    return round(min(0.95, 0.45 + ratio * 0.4 + min(count, 10) * 0.03), 2)


def _categorize_suggestion(
    target: str,
    description: str,
    category: str,
    email_ids: tuple[str, ...],
    confidence: float,
) -> Suggestion:
    return Suggestion(
        action="categorize",
        target=target,
        description=description,
        confidence=confidence,
        category=category,
        requires_write=False,
        email_ids=email_ids,
    )


def sample_for_analysis(emails: list[dict], limit: int = 200) -> list[dict]:
    """Return a bounded sample of emails for analysis on very large selections.

    Analysis stays cheap for 10k+ selections while suggestions still describe
    the overall pattern. When the selection fits, it is returned unchanged.
    """
    if len(emails) <= limit:
        return emails
    step = len(emails) / limit
    return [emails[int(i * step)] for i in range(limit)]


def generate_suggestions(
    emails: list[dict],
    infer: Callable[[str], str] | None = None,
    confidence_threshold: float = 0.0,
    sample_limit: int = 200,
) -> list[Suggestion]:
    """Generate batch action suggestions for a selection of emails.

    Deterministic pattern matching runs first. When *infer* is provided it may
    add an AI-identified pattern; failures fall back to deterministic results.
    Selections larger than *sample_limit* are sampled for analysis, and
    suggestions below *confidence_threshold* are dropped.
    """
    if not emails:
        return []
    analysis_set = sample_for_analysis(emails, sample_limit)
    total = len(emails)
    summary = analyze_batch(analysis_set)
    suggestions: list[Suggestion] = []

    # Dominant sender → categorize together.
    for sender, count in summary["senders"].most_common(3):
        if count < 2:
            continue
        ids = tuple(
            e["id"]
            for e in emails
            if (e.get("sender_name") or e.get("sender_email") or "").strip() == sender
        )
        cats = Counter(
            c
            for e in emails
            if e["id"] in ids
            for c in (
                e.get("categories") or [e["category"]] if e.get("category") else []
            )
        )
        dominant = cats.most_common(1)[0][0] if cats else None
        if dominant:
            suggestions.append(
                _categorize_suggestion(
                    f"sender: {sender}",
                    f"{count} emails from {sender} share category {dominant}",
                    dominant,
                    ids,
                    _confidence(count, total),
                )
            )

    # Shared user label → categorize together.
    for label, count in summary["labels"].most_common(3):
        if count < 2:
            continue
        ids = tuple(e["id"] for e in emails if label in (e.get("labels") or ()))
        cats = Counter(
            c
            for e in emails
            if e["id"] in ids
            for c in (
                e.get("categories") or [e["category"]] if e.get("category") else []
            )
        )
        dominant = cats.most_common(1)[0][0] if cats else None
        if dominant:
            suggestions.append(
                _categorize_suggestion(
                    f"label: {label}",
                    f"{count} emails under label {label} share category {dominant}",
                    dominant,
                    ids,
                    _confidence(count, total),
                )
            )

    # Dominant domain → suggest mutating action (read-only for now).
    for domain, count in summary["domains"].most_common(3):
        if count < 3:
            continue
        ids = tuple(
            e["id"] for e in emails if (e.get("sender_domain") or "").strip() == domain
        )
        suggestions.append(
            Suggestion(
                action="archive",
                target=f"domain: {domain}",
                description=f"{count} emails from {domain} — could be archived",
                confidence=_confidence(count, total),
                requires_write=True,
                email_ids=ids,
            )
        )
        suggestions.append(
            Suggestion(
                action="mark-read",
                target=f"domain: {domain}",
                description=f"Mark {count} emails from {domain} as read",
                confidence=_confidence(count, total),
                requires_write=True,
                email_ids=ids,
            )
        )

    # Deterministic bulk pattern: many newsletters → delete suggestion.
    newsletter_ids = tuple(
        e["id"]
        for e in emails
        if any(
            token in (e.get("subject") or "").lower()
            for token in ("unsubscribe", "newsletter", "digest")
        )
    )
    if len(newsletter_ids) >= 3:
        suggestions.append(
            Suggestion(
                action="delete",
                target="newsletters",
                description=f"{len(newsletter_ids)} newsletters could be deleted",
                confidence=_confidence(len(newsletter_ids), total),
                requires_write=True,
                email_ids=newsletter_ids,
            )
        )

    # Optional AI pass.
    if infer is not None:
        try:
            ai = infer(
                "Identify a batch action pattern across these emails and reply "
                "with one line: '<action>: <target> (<count> emails)'. Actions: "
                "categorize, archive, mark-read, delete."
            )
            if ai.strip():
                suggestions.append(
                    Suggestion(
                        action="categorize",
                        target="ai pattern",
                        description=ai.strip()[:200],
                        confidence=0.6,
                        requires_write=False,
                        email_ids=tuple(e["id"] for e in emails),
                    )
                )
        except Exception:  # noqa: BLE001, S110 - inference is best-effort
            pass

    if confidence_threshold > 0.0:
        suggestions = [s for s in suggestions if s.confidence >= confidence_threshold]
    return suggestions


def cache_key(emails: list[dict]) -> tuple[Any, ...]:
    """Stable cache key for a selection of emails."""
    return tuple(sorted(e["id"] for e in emails))
