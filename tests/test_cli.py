from maily.cli import render_human


def test_human_output_shows_action_required_email_details():
    """Test that Action Required emails show subject and sender in human-readable output"""
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
    assert "Action Required: 1" in output
    assert "Newsletters: 1" in output


def test_human_output_handles_empty_subject_in_action_required():
    """Test that empty subject is displayed as '(no subject)' in Action Required emails"""
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


def test_human_output_no_action_required_shows_only_counts():
    """Test that categories without Action Required only show counts"""
    output = render_human(
        {
            "status": "completed",
            "messages": [
                {
                    "subject": "Newsletter",
                    "sender_email": "news@example.com",
                    "body": "Daily news",
                    "category": "Newsletters",
                },
            ],
            "counts": {"Newsletters": 1, "Work": 0},
            "categories": {
                "Newsletters": [
                    {
                        "subject": "Newsletter",
                        "sender_email": "news@example.com",
                        "body": "Daily news",
                    }
                ],
                "Work": [],
            },
            "historical_counts": {"deferred": False},
            "errors": [],
        }
    )
    assert "Newsletters: 1" in output
    assert "Work: 0" in output
    # Should NOT have email details for non-Action Required categories
    assert "Newsletter (news@example.com)" not in output


def test_human_output_other_categories_unchanged():
    """Test that existing behavior for other categories is unchanged"""
    output = render_human(
        {
            "status": "completed",
            "messages": [],
            "counts": {"Work": 5, "Personal": 3},
            "categories": {},
            "historical_counts": {"deferred": False},
            "errors": [],
        }
    )
    assert "Work: 5" in output
    assert "Personal: 3" in output
    assert "Scan: completed" in output
