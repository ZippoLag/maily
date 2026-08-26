## Purpose

Scans the Gmail spam folder for new emails and presents them to the user for review and action. This capability is part of the spam handling workflow that was originally specified but deferred from v1.

## ADDED Requirements

### Requirement: Spam folder synchronization

The system SHALL retrieve unread messages from the Gmail spam folder during daily scans and SHALL present them separately from inbox messages.

#### Scenario: Spam messages present
- **WHEN** a scan includes the spam folder
- **THEN** new unread messages in spam are identified and listed

#### Scenario: Empty spam folder
- **WHEN** a scan finds no unread messages in spam
- **THEN** the system reports zero spam messages

### Requirement: Spam message identification

The system SHALL distinguish between inbox and spam messages in all outputs (CLI, TUI, JSON) and SHALL never classify spam messages using the standard category rules.

#### Scenario: Spam vs inbox separation
- **WHEN** displaying scan results
- **THEN** spam messages appear in a separate "Spam" section from category results

## DEFERRAL NOTICE

**This specification is captured for completeness but implementation is DEFERRED** until after `static-analysis-category-learning` and TUI improvements are complete. See `proposal.md` for deferral rationale.
