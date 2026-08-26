from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

STOP_WORDS = frozenset(
    """a about after again all am an and any are as at be because been before being
    between both but by can could did do does doing down during each few for from
    further had has have having he her here hers herself him himself his how i if in
    into is it its itself just me more most my myself no nor not now of off on once
    only or other our ours ourselves out over own same she should so some such than
    that the their theirs them themselves then there these they this those through to
    too under until up very was we were what when where which while who whom why will
    with would you your yours yourself yourselves""".split()
)


def extract_words(text: str) -> list[str]:
    """Split text into lowercase words on non-alphanumeric boundaries."""
    return [word for word in re.split(r"[^a-z0-9]+", text.lower()) if word]


def word_frequencies(contents: list[str]) -> Counter:
    """Count documents containing each word across email contents, excluding stop words.

    A word counts once per document, so the count reflects how many emails
    contain the pattern rather than how many times it occurs.
    """
    counter: Counter = Counter()
    for content in contents:
        counter.update(word for word in set(extract_words(content)) if word not in STOP_WORDS)
    return counter


def generate_suggestions(database, min_count: int = 3) -> list[dict]:
    """Suggest rule patterns from user category overrides.

    For each category the user has assigned, counts words across the overridden
    emails' subjects and bodies, and returns words appearing in at least
    ``min_count`` emails as (category, pattern, count) suggestions.
    """
    rows = database.connection.execute(
        "SELECT o.categories, m.subject, m.body "
        "FROM user_category_overrides o JOIN messages m ON m.id = o.message_id"
    ).fetchall()
    contents_by_category: dict[str, list[str]] = {}
    for row in rows:
        categories = json.loads(row[0])
        content = f"{row[1]}\n{row[2]}"
        for category in categories:
            contents_by_category.setdefault(category, []).append(content)
    suggestions: list[dict] = []
    for category, contents in contents_by_category.items():
        frequencies = word_frequencies(contents)
        for word, count in frequencies.most_common():
            if count < min_count:
                break
            suggestions.append({"category": category, "pattern": word, "count": count})
    return suggestions


def add_rule_to_config(config_file: Path, category: str, patterns: list[str]) -> None:
    """Append a [[classification.rules]] block to config.toml."""
    block = (
        f"\n[[classification.rules]]\n"
        f"category = {json.dumps(category)}\n"
        f"patterns = {json.dumps(patterns)}\n"
    )
    with config_file.open("a", encoding="utf-8") as stream:
        stream.write(block)


def accept_suggestion(database, config_file: Path, suggestion_id: int) -> dict | None:
    """Add an accepted suggestion to the user config and mark it accepted."""
    suggestion = next(
        (row for row in database.get_rule_suggestions() if row["id"] == suggestion_id),
        None,
    )
    if suggestion is None:
        return None
    add_rule_to_config(config_file, suggestion["category"], [suggestion["pattern"]])
    database.update_rule_suggestion_status(suggestion_id, "accepted")
    return {"category": suggestion["category"], "pattern": suggestion["pattern"]}


def reject_suggestion(database, suggestion_id: int) -> bool:
    """Mark a suggestion as rejected."""
    if not any(row["id"] == suggestion_id for row in database.get_rule_suggestions()):
        return False
    database.update_rule_suggestion_status(suggestion_id, "rejected")
    return True
