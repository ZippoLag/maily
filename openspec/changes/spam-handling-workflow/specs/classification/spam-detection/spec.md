## Purpose

Detects potential spam emails in the inbox that Gmail's filters may have missed, allowing users to confirm and take action. This addresses the original requirement to "display them in a list, asking user for confirmation on which to flag."

## ADDED Requirements

### Requirement: Inbox spam detection

The system SHALL identify unread inbox emails that exhibit spam-like characteristics (based on sender, subject, content patterns) and SHALL present them to the user for confirmation.

#### Scenario: Potential spam in inbox
- **WHEN** an unread inbox email matches spam-like patterns
- **THEN** the email is flagged for user review as potential spam

#### Scenario: User confirmation
- **WHEN** user reviews flagged emails
- **THEN** user can confirm as spam or mark as not-spam

### Requirement: Spam pattern library

The system SHALL maintain a library of common spam patterns (sender domains, subject keywords, body content) to identify potential spam in inbox.

#### Scenario: Known spam sender
- **WHEN** email is from a known spam domain
- **THEN** it is flagged for user review

## DEFERRAL NOTICE

**This specification is captured for completeness but implementation is DEFERRED** until after `static-analysis-category-learning` and TUI improvements are complete. See `proposal.md` for deferral rationale.
