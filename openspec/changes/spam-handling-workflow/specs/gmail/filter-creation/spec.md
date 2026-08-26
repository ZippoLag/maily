## Purpose

Creates Gmail filter rules based on user confirmation of spam emails, allowing maily to automatically filter similar emails in the future. This addresses the original requirement to "create a rule so gmail correctly filters them from now on."

## ADDED Requirements

### Requirement: Filter creation from user confirmation

The system SHALL create Gmail filter rules when the user confirms that an email is spam and requests automatic filtering for similar messages.

#### Scenario: User confirms spam and requests filter
- **WHEN** user identifies an email as spam and chooses to create a filter
- **THEN** the system creates a Gmail filter matching the sender, subject patterns, or other criteria

#### Scenario: Filter applies to future emails
- **WHEN** a Gmail filter is created for a spam sender
- **THEN** future emails from that sender are automatically moved to spam

### Requirement: Filter criteria extraction

The system SHALL extract filter criteria from confirmed spam emails, including sender email, sender domain, and subject keywords.

#### Scenario: Sender-based filter
- **WHEN** user creates filter from spam email
- **THEN** the filter targets the sender email or domain

## DEFERRAL NOTICE

**This specification is captured for completeness but implementation is DEFERRED** until after `static-analysis-category-learning` and TUI improvements are complete. See `proposal.md` for deferral rationale.

**NOTE**: This requires Gmail API write scopes and is a BREAKING change from the current read-only architecture.
