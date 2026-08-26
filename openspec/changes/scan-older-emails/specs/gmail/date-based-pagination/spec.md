## Purpose

Processes historical emails in date-based chunks rather than loading all at once, ensuring the system remains responsive and provides progress visibility for large mailboxes.

## ADDED Requirements

### Requirement: Chunked date processing

The sync system SHALL divide historical date ranges into chunks (day, week, month, year) and SHALL process one chunk at a time.

#### Scenario: Day-based chunking
- **WHEN** user selects day-based pagination
- **THEN** each day's emails are fetched and processed as a unit

#### Scenario: Week-based chunking
- **WHEN** user selects week-based pagination
- **THEN** each week's emails are fetched and processed as a unit

### Requirement: Configurable chunk size

The system SHALL allow users to configure the chunk size (day/week/month/year) and SHALL default to day-based chunking.

#### Scenario: User selects week chunks
- **WHEN** user configures chunk_size = "week"
- **THEN** system uses week-based chunks

#### Scenario: Default to day chunks
- **WHEN** no chunk size is configured
- **THEN** system uses day-based chunks

### Requirement: Chunk progress reporting

The system SHALL report progress at the chunk level, showing which date range is currently being processed and how many chunks remain.

#### Scenario: Processing day 5 of 30
- **WHEN** system processes the 5th day of a 30-day range
- **THEN** progress shows "Processing day 5/30: 2024-01-05"

#### Scenario: Processing week 2 of 4
- **WHEN** system processes the 2nd week of a 1-month range
- **THEN** progress shows "Processing week 2/4: 2024-01-08 to 2024-01-14"
