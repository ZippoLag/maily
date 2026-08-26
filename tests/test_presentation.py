from maily.cli import render_human
from maily.tui import grouped_rows


def test_human_output_marks_historical_counts_deferred():
    output = render_human(
        {
            "status": "completed",
            "messages": [],
            "counts": {"Other": 0},
            "historical_counts": {"deferred": True},
            "errors": [],
        }
    )
    assert "deferred" in output


def test_tui_projection_groups_and_sorts_without_mutations():
    rows = [
        {
            "category": "Work",
            "subject": "Older",
            "last_received_at": "2026-08-25T08:00:00",
            "importance": 1,
            "sender_name": "B",
            "sender_domain": "b.test",
        },
        {
            "category": "Work",
            "subject": "Newer",
            "last_received_at": "2026-08-25T09:00:00",
            "importance": 2,
            "sender_name": "A",
            "sender_domain": "a.test",
        },
    ]
    grouped = grouped_rows(rows, ["Work", "Other"])
    assert [row["subject"] for row in grouped["Work"]] == ["Newer", "Older"]
    assert grouped["Other"] == []


def test_human_output_shows_action_required_email_details():
    output = render_human(
        {
            "status": "completed",
            "messages": [
                {
                    "subject": "Important Meeting",
                    "sender_email": "boss@example.com",
                    "body": "Please attend",
                    "category": "Action Required",
                },
                {
                    "subject": "Newsletter",
                    "sender_email": "news@example.com",
                    "body": "Daily news",
                    "category": "Newsletters",
                },
            ],
            "counts": {"Action Required": 1, "Newsletters": 1},
            "categories": {
                "Action Required": [
                    {
                        "subject": "Important Meeting",
                        "sender_email": "boss@example.com",
                        "body": "Please attend",
                    }
                ],
                "Newsletters": [
                    {
                        "subject": "Newsletter",
                        "sender_email": "news@example.com",
                        "body": "Daily news",
                    }
                ],
            },
            "historical_counts": {"deferred": False},
            "errors": [],
        }
    )
    assert "Important Meeting (boss@example.com)" in output


def test_human_output_handles_empty_subject_in_action_required():
    output = render_human(
        {
            "status": "completed",
            "messages": [
                {
                    "subject": "",
                    "sender_email": "test@example.com",
                    "body": "Test",
                    "category": "Action Required",
                },
            ],
            "counts": {"Action Required": 1},
            "categories": {
                "Action Required": [
                    {"subject": "", "sender_email": "test@example.com", "body": "Test"}
                ]
            },
            "historical_counts": {"deferred": False},
            "errors": [],
        }
    )
    assert "(no subject) (test@example.com)" in output
