from datetime import UTC, datetime

from maily.config import Rule
from maily.models import EmailMessage


def make_message(
    subject: str = "", body: str = "", sender_email: str = ""
) -> EmailMessage:
    return EmailMessage(
        "1",
        "t",
        "",
        sender_email,
        sender_email.split("@")[-1] if sender_email else "",
        subject,
        body,
        datetime.now(UTC),
        True,
        False,
    )


def test_rule_matches_tracks_which_patterns_matched():
    rule = Rule("Action Required", ("verify", "due date", "urgent"))
    message = make_message(subject="Please verify your account")
    assert rule.matches(message) == ("verify",)


def test_rule_matches_records_all_matched_patterns_in_order():
    rule = Rule("Action Required", ("verify", "due date"))
    message = make_message(subject="URGENT: verify due date")
    assert rule.matches(message) == ("verify", "due date")


def test_rule_matches_returns_empty_when_nothing_matches():
    rule = Rule("Action Required", ("verify", "due date"))
    message = make_message(subject="Hello world")
    assert rule.matches(message) == ()
