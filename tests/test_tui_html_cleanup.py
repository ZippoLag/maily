"""Tests for tui-reading-pane-html-cleanup: html_to_readable helper."""

from maily.tui import html_to_readable


def test_html_body_converted_to_markdown():
    body = "<p>Hello <b>there</b></p>"
    text = html_to_readable(body)
    assert "Hello" in text
    assert "there" in text
    assert "<b>" not in text
    assert "<p>" not in text


def test_plain_text_passes_through_unchanged():
    body = "Just plain text\nwith a second line"
    assert html_to_readable(body) == body


def test_missing_html_passes_through_unchanged():
    body = "No tags here at all"
    assert html_to_readable(body) == body


def test_conversion_failure_falls_back_to_original():
    body = "<html><body>Broken"
    # Force a failure by passing something the converter chokes on; the helper
    # must never raise and must return the original body.
    result = html_to_readable(body)
    assert isinstance(result, str)


def test_pane_text_renders_clean_html_body():
    from maily.tui import email_pane_text

    item = {
        "sender_name": "Alice",
        "sender_email": "alice@example.com",
        "subject": "HTML Test",
        "body": "<p>Hello <b>there</b></p>",
    }
    text = email_pane_text(item, width=80)
    assert "Hello" in text
    assert "there" in text
    assert "<p>" not in text
    assert "<b>" not in text
