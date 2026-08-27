"""Tests for tui-email-body-wrapping: pane text helper and layout."""

from maily.tui import email_pane_text


def test_pane_text_includes_sender_and_subject():
    item = {
        "sender_name": "Alice",
        "sender_email": "alice@example.com",
        "subject": "Hello World",
        "body": "Short body.",
    }
    text = email_pane_text(item, width=80)
    assert "Alice" in text
    assert "alice@example.com" in text
    assert "Hello World" in text
    assert "Short body." in text


def test_pane_text_empty_body_shows_placeholder():
    item = {
        "sender_name": "Bob",
        "sender_email": "bob@example.com",
        "subject": "Empty",
        "body": "",
    }
    text = email_pane_text(item, width=80)
    assert "(no body)" in text


def test_pane_text_none_body_shows_placeholder():
    item = {
        "sender_name": "Bob",
        "sender_email": "bob@example.com",
        "subject": "No Body",
        "body": None,
    }
    text = email_pane_text(item, width=80)
    assert "(no body)" in text


def test_pane_text_preserves_paragraph_breaks():
    item = {
        "sender_name": "Alice",
        "sender_email": "alice@example.com",
        "subject": "Paragraphs",
        "body": "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.",
    }
    text = email_pane_text(item, width=80)
    assert "First paragraph." in text
    assert "Second paragraph." in text
    assert "Third paragraph." in text


def test_pane_text_wraps_long_lines():
    long_body = "word " * 40  # 200 chars, should wrap at width 40
    item = {
        "sender_name": "Alice",
        "sender_email": "alice@example.com",
        "subject": "Wrap Test",
        "body": long_body,
    }
    text = email_pane_text(item, width=40)
    lines = text.split("\n")
    # At least some lines should be <= width (accounting for "From:" prefix)
    non_header_lines = [
        l for l in lines if not l.startswith("From:") and not l.startswith("Subject:")
    ]
    # The body should have been wrapped into multiple lines
    assert len(non_header_lines) > 1
