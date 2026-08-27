## Purpose

Processes emails in configurable batches to handle large volumes efficiently, providing regular checkpoints and progress updates.

## ADDED Requirements

### Requirement: Batch processing

The sync system SHALL process emails in batches with configurable batch size, defaulting to 100 emails per batch.

#### Scenario: Default batch size
- **WHEN** no batch size is configured
- **THEN** system uses 100 emails per batch

#### Scenario: Custom batch size
- **WHEN** user configures batch_size = 500
- **THEN** system processes 500 emails per batch

### Requirement: Checkpoint after each batch

The system SHALL save state after each batch completes, creating a resume point.

#### Scenario: Checkpoint on batch complete
- **WHEN** a batch finishes processing
- **THEN** system saves checkpoint with last email ID and timestamp

#### Scenario: Checkpoint on error
- **WHEN** a batch encounters an error
- **THEN** system saves checkpoint before the error and reports the error

### Requirement: Configurable batch size

Users SHALL be able to configure batch size based on their Gmail quota and system resources.

#### Scenario: Set batch size in config
- **WHEN** user sets batch_size = 200 in config.toml
- **THEN** system uses 200 emails per batch

#### Scenario: CLI override of batch size
- **WHEN** user provides --batch-size 500
- **THEN** system uses 500 for this scan, ignoring config

### Requirement: Batch progress reporting

The system SHALL report progress at the batch level, showing batch number, emails processed, and rate.

#### Scenario: Batch completion message
- **WHEN** a batch completes
- **THEN** progress shows "Batch 5/50 complete: 500 emails processed"

#### Scenario: Rate display
- **WHEN** multiple batches complete
- **THEN** progress shows "500 emails, 100 emails/sec"

### Requirement: Memory cleanup between batches

The system SHALL clear memory between batches to prevent memory buildup during long-running scans.

#### Scenario: Clear cache between batches
- **WHEN** a batch completes
- **THEN** system clears temporary caches and data

#### Scenario: Bounded memory usage
- **WHEN** processing large scan
- **THEN** memory usage stays within expected bounds regardless of total emails
