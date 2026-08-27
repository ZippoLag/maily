# sync/long-running-mode Specification

## Purpose

Enables processing large email backlogs (1000s of emails) in a long-running mode suitable for overnight execution, with progress tracking and resumption capability.

## Requirements

### Requirement: Long-running scan mode

The system SHALL support a long-running scan mode that can process large numbers of emails over an extended period, suitable for overnight execution.

#### Scenario: Overnight scan
- **WHEN** user starts scan with --long-running flag
- **THEN** system processes emails without timeout constraints

#### Scenario: Background processing
- **WHEN** long-running scan is active
- **THEN** system continues processing even if TUI is not active

### Requirement: Progress persistence

The system SHALL periodically save progress during long-running scans so that processing can resume if interrupted.

#### Scenario: Save progress every N emails
- **WHEN** processing long-running scan
- **THEN** progress is saved to database every 100 emails (configurable)

#### Scenario: Resume from checkpoint
- **WHEN** long-running scan is restarted after interruption
- **THEN** system resumes from last checkpoint, not from beginning

### Requirement: Extended timeout handling

The system SHALL handle extended timeouts appropriately for long-running operations, different from standard scan timeouts.

#### Scenario: No arbitrary timeout
- **WHEN** long-running scan is active
- **THEN** individual Gmail API calls respect rate limits but overall scan has no timeout

#### Scenario: Graceful interruption
- **WHEN** user interrupts long-running scan (Ctrl+C)
- **THEN** system saves current progress before exiting

### Requirement: Progress logging

The system SHALL log progress to a file during long-running scans for later review.

#### Scenario: Log file creation
- **WHEN** long-running scan starts
- **THEN** a progress log file is created in ~/.maily/logs/

#### Scenario: Log progress entries
- **WHEN** processing each chunk
- **THEN** log file receives timestamped progress entries

### Requirement: Completion notification

The system SHALL provide notification when long-running scan completes, even if started from CLI.

#### Scenario: CLI completion message
- **WHEN** long-running scan completes in CLI
- **THEN** final summary is printed with total counts

#### Scenario: TUI notification on completion
- **WHEN** long-running scan completes while TUI is open
- **THEN** TUI shows notification with completion status
