## Purpose

Provides immediate visibility into action-required emails by displaying their title and sender in the default CLI scan output, making urgent messages actionable without requiring TUI or JSON parsing.

## ADDED Requirements

### Requirement: Display Action Required email details in CLI

The CLI SHALL display the subject (title) and sender for each email in the "Action Required" category when showing human-readable scan output. Each email SHALL be displayed on a separate line with the format: "- <subject> (<sender_email>)".

#### Scenario: Single Action Required email
- **WHEN** the scan returns one email in the "Action Required" category
- **THEN** the human-readable output shows that email's subject and sender under the "Action Required" category line

#### Scenario: Multiple Action Required emails
- **WHEN** the scan returns multiple emails in the "Action Required" category
- **THEN** the human-readable output shows each email's subject and sender on separate lines under the "Action Required" category line

#### Scenario: Action Required email with empty subject
- **WHEN** an email in the "Action Required" category has an empty subject
- **THEN** the human-readable output displays "(no subject)" for the subject and still shows the sender

#### Scenario: JSON format unchanged
- **WHEN** the user runs scan with `--json-format`
- **THEN** the JSON output structure remains unchanged and does not include the expanded human-readable formatting
