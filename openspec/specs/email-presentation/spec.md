# email-presentation Specification

## Purpose
Makes daily triage results usable from scripts, terminals, and an initial read-only interactive interface without performing Gmail mutations.

## Requirements

### Requirement: Human-readable scan output

The CLI SHALL display today's scan status, category counts, classification degradation, and deferred historical counts in a human-readable format.

#### Scenario: Partial initial dataset
- **WHEN** only today's unread messages have been synchronized
- **THEN** the output labels older unread and read counts as deferred rather than displaying them as zero

### Requirement: JSON scan output

The CLI SHALL provide a `--json-format` option that emits machine-readable output containing synchronization status, messages, categories, counts, and errors without decorative formatting.

#### Scenario: JSON consumer
- **WHEN** the user runs a supported scan command with `--json-format`
- **THEN** stdout contains valid JSON and diagnostics are represented as structured fields

### Requirement: Read-only TUI browsing

The TUI SHALL allow the user to browse categories, expand and collapse their messages, inspect message details, and sort results by first-thread date, last-thread date, inferred importance or urgency, sender name, and sender domain. Additionally, the TUI SHALL support multi-select for batch operations and SHALL display Gmail labels as badges.

#### Scenario: Browse with multi-select
- **WHEN** the user opens the TUI after a scan
- **THEN** the user can select multiple emails and perform batch operations

#### Scenario: Label badges visible
- **WHEN** viewing emails in TUI
- **THEN** Gmail labels are displayed as badges on each email

#### Scenario: TUI mutation attempt
- **WHEN** the user views a message in the TUI
- **THEN** no Gmail mutation control is offered and no message state is changed by browsing

### Requirement: Action transparency

The initial presentation layer SHALL clearly distinguish synchronized data, cached classifications, deferred historical data, and errors requiring user action.

#### Scenario: Degraded scan
- **WHEN** Gmail or Ollama is unavailable for part of a scan
- **THEN** the CLI and TUI identify the affected portion and retain access to valid local results