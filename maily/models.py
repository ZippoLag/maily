from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import Rule


@dataclass(frozen=True)
class EmailMessage:
    id: str
    thread_id: str
    sender_name: str
    sender_email: str
    sender_domain: str
    subject: str
    body: str
    received_at: datetime
    unread: bool
    is_spam: bool
    importance: float | None = None

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["received_at"] = self.received_at.isoformat()
        return result


def primary_category(categories: list[str] | tuple[str, ...]) -> str | None:
    """Return the primary category for an email.

    Categories must be passed in precedence order: user-assigned categories
    first (in assignment order), then rule-matched categories (in rule
    definition order). The first entry is the primary category.
    """
    return categories[0] if categories else None


@dataclass
class ClassificationResult:
    categories: list[str]
    source: str
    cached: bool = False
    degraded: bool = False
    error: str | None = None
    matched_rules: tuple[Rule, ...] = ()


@dataclass
class ScanResult:
    started_at: str
    completed_at: str | None
    status: str
    messages: list[EmailMessage] = field(default_factory=list)
    classifications: dict[str, ClassificationResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    historical_counts_deferred: bool = True
    category_names: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        categories: dict[str, list[dict[str, Any]]] = {}
        for message in self.messages:
            result = self.classifications.get(
                message.id, ClassificationResult(["Other"], "fallback")
            )
            for category in result.categories:
                categories.setdefault(category, []).append(message.as_dict())
        counts = {
            category: len(categories.get(category, []))
            for category in self.category_names
        }
        counts.update(
            {
                category: len(items)
                for category, items in categories.items()
                if category not in counts
            }
        )
        return {
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "messages": [message.as_dict() for message in self.messages],
            "classifications": {
                message_id: asdict(result)
                for message_id, result in self.classifications.items()
            },
            "categories": categories,
            "counts": counts,
            "historical_counts": {
                "unread_previously_existing": None,
                "read": None,
                "deferred": self.historical_counts_deferred,
            },
            "errors": self.errors,
        }
