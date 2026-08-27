## Purpose

Tracks historical sync progress across sessions so users can resume long-running scans and see where they left off.

## ADDED Requirements

### Requirement: Sync state persistence

The system SHALL persist sync state including last processed date, total emails processed, and current position.

#### Scenario: Resume interrupted scan
- **WHEN** user starts a scan after previous was interrupted
- **THEN** system resumes from where it left off

#### Scenario: Track sync progress
- **WHEN** user runs historical scan
- **THEN** progress is saved periodically

### Requirement: Per-mailbox sync state

The system SHALL track sync state separately for each Gmail account (when multi-account support is added).

#### Scenario: Multiple accounts
- **WHEN** user has multiple Gmail accounts
- **THEN** each account has its own sync state

#### Scenario: Single account for v1
- **WHEN** only one account is configured (v1)
- **THEN** sync state is stored for that single account

### Requirement: Sync state query

The system SHALL provide a way to query current sync state (last sync date, emails processed, etc.).

#### Scenario: Check sync status
- **WHEN** user runs status command
- **THEN** system reports last sync date and progress

#### Scenario: CLI status output
- **WHEN** running `maily status`
- **THEN** CLI shows sync state information

### Requirement: Sync state reset

The system SHALL allow users to reset sync state to start fresh.

#### Scenario: Reset sync state
- **WHEN** user requests sync state reset
- **THEN** system clears progress and starts from beginning

#### Scenario: Confirm reset
- **WHEN** user attempts to reset sync state
- **THEN** system asks for confirmation before resetting
