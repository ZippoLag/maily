# tui/email-line-format Specification

## Purpose

Defines the standard textual layout of an email row in the list so each line is scannable and shows mark state, sender, and subject at a glance.

## Requirements

### Requirement: Email line format

Each email row SHALL render, in order: the mark state, the sender summary, then the subject. The mark state SHALL be rendered as `[ ]` (unmarked) or `[x]` (marked). The sender summary SHALL be the first sender address, prefixed with `... ` when the message has more than one sender.

#### Scenario: Single-sender unmarked line

- **WHEN** an unmarked email has one sender `alice@example.com` and subject `Hello`
- **THEN** the row renders as `[ ] alice@example.com Hello`

#### Scenario: Multi-sender marked line

- **WHEN** a marked email has senders `a@x.com, b@x.com` and subject `Update`
- **THEN** the row renders as `[x] ... a@x.com Update`