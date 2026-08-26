from maily.config import DEFAULT_CATEGORIES, load_config
from maily.db import Database
from maily.learning import STOP_WORDS, extract_words, generate_suggestions, word_frequencies


def test_stop_words_include_common_english_words():
    for word in ("the", "a", "an", "and", "is", "in", "on", "of", "to", "for"):
        assert word in STOP_WORDS


def test_extract_words_splits_on_non_alphanumeric():
    assert extract_words("Invoice-2024 #1: Payment due!") == ["invoice", "2024", "1", "payment", "due"]


def test_extract_words_lowercases():
    assert extract_words("URGENT Reminder") == ["urgent", "reminder"]


def test_word_frequencies_counts_documents_not_occurrences():
    contents = [
        "The invoice is overdue",
        "Invoice reminder",
        "Invoice number 2",
    ]
    frequencies = word_frequencies(contents)
    assert frequencies["invoice"] == 3
    assert frequencies["overdue"] == 1
    assert "the" not in frequencies  # stop word filtered
    assert "is" not in frequencies  # stop word filtered


def test_generate_suggestions_only_at_threshold(tmp_path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    for message_id, subject in (("m1", "Team meeting at noon"), ("m2", "Team sync invite"), ("m3", "Team retro")):
        database.connection.execute("INSERT INTO threads(id) VALUES (?)", (message_id,))
        database.connection.execute(
            "INSERT INTO messages(id, thread_id, subject, body, received_at, unread, is_spam, synced_at) "
            "VALUES (?, ?, ?, '', '2026-08-26T10:00:00', 0, 0, '2026-08-26T10:00:00')",
            (message_id, message_id, subject),
        )
    database.connection.commit()
    database.set_user_override("m1", ["Work"])
    database.set_user_override("m2", ["Work"])
    database.set_user_override("m3", ["Work"])
    suggestions = generate_suggestions(database, min_count=3)
    by_category = {suggestion["category"]: suggestion for suggestion in suggestions}
    assert by_category["Work"]["pattern"] == "team"
    assert by_category["Work"]["count"] == 3
    # a word appearing in fewer than threshold emails is not suggested
    assert all(suggestion["count"] >= 3 for suggestion in suggestions)
    database.close()


def test_generate_suggestions_no_suggestions_below_threshold(tmp_path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    database.connection.execute("INSERT INTO threads(id) VALUES ('m1')")
    database.connection.execute(
        "INSERT INTO messages(id, thread_id, subject, body, received_at, unread, is_spam, synced_at) "
        "VALUES ('m1', 'm1', 'Lunch plans', '', '2026-08-26T10:00:00', 0, 0, '2026-08-26T10:00:00')"
    )
    database.connection.commit()
    database.set_user_override("m1", ["Personal"])
    suggestions = generate_suggestions(database, min_count=3)
    assert suggestions == []
    database.close()
