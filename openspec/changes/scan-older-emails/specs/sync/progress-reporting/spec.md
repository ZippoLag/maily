## Purpose

Provides real-time progress feedback during large scans so users know the system is working and can estimate completion time, addressing the requirement to not "hang silently."

## ADDED Requirements

### Requirement: Real-time progress display

The sync system SHALL display progress information in real-time during scan operations, including count of emails fetched, date range being processed, and estimated time remaining.

#### Scenario: Scan in progress
- **WHEN** a scan is processing emails
- **THEN** the CLI/TUI shows progress updates at least every 5 seconds

#### Scenario: Progress includes counts
- **WHEN** processing a chunk of emails
- **THEN** progress shows emails fetched in current chunk and total so far

### Requirement: Progress in CLI

The CLI SHALL output progress information to stdout during long-running scans.

#### Scenario: CLI progress output
- **WHEN** running `maily scan --long-running`
- **THEN** CLI prints progress lines like "Fetched 50/1000 emails..."

#### Scenario: CLI JSON format excludes progress
- **WHEN** running with `--json-format`
- **THEN** progress is logged but not included in JSON output

### Requirement: Progress in TUI

The TUI SHALL display a progress bar or status indicator during long-running scans.

#### Scenario: TUI progress bar
- **WHEN** scan is running in TUI
- **THEN** a progress bar shows completion percentage

#### Scenario: TUI status message
- **WHEN** scan is running
- **THEN** status shows "Scanning: 25% complete, 250/1000 emails"

### Requirement: Estimated time remaining

The system SHALL calculate and display estimated time remaining based on processing rate.

#### Scenario: ETA display
- **WHEN** processing at 100 emails/minute with 500 remaining
- **THEN** progress shows "~5 minutes remaining"

#### Scenario: ETA updates
- **WHEN** processing rate changes
- **THEN** ETA recalculates and updates
