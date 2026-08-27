# sync/error-resilience Specification

## Purpose

Ensures the system can handle errors gracefully during large scans, continuing processing where possible and reporting issues at the end.

## Requirements

### Requirement: Continue on individual email errors

The system SHALL continue processing other emails if one email fails to process, rather than stopping the entire scan.

#### Scenario: One email fails
- **WHEN** email N fails to process
- **THEN** system logs the error, skips to email N+1, continues scan

#### Scenario: Multiple emails fail
- **WHEN** 5 emails in a batch fail
- **THEN** system logs all 5 errors, continues with next batch

### Requirement: Aggregate error reporting

The system SHALL collect all errors during a scan and SHALL report them at the end, not stopping for individual errors.

#### Scenario: Error summary at completion
- **WHEN** scan completes with errors
- **THEN** system displays count of errors and list of failed email IDs

#### Scenario: Error details available
- **WHEN** scan completes with errors
- **THEN** user can view detailed error information for each failure

### Requirement: Error classification

The system SHALL classify errors into categories (network, quota, parsing, etc.) for better troubleshooting.

#### Scenario: Network error classification
- **WHEN** a network timeout occurs
- **THEN** error is classified as network error

#### Scenario: Quota error classification
- **WHEN** Gmail quota is exceeded
- **THEN** error is classified as quota error

### Requirement: Retry for transient errors

The system SHALL automatically retry transient errors (network timeouts, rate limits) with exponential backoff.

#### Scenario: Automatic retry on timeout
- **WHEN** a network timeout occurs
- **THEN** system retries after delay, with exponential backoff

#### Scenario: Max retries limit
- **WHEN** an email fails after max retries (default: 3)
- **THEN** system logs as permanent failure, continues to next email

### Requirement: Partial success reporting

The system SHALL report partial success when some emails are processed but others fail.

#### Scenario: Partial success message
- **WHEN** scan completes with some errors
- **THEN** message shows "Processed 950/1000 emails (50 errors)"

#### Scenario: Partial success exit code
- **WHEN** scan completes with errors
- **THEN** CLI exits with code 1 (error) but still reports partial success

### Requirement: Error log file

The system SHALL write detailed error information to a log file for post-scan review.

#### Scenario: Error log creation
- **WHEN** errors occur during scan
- **THEN** errors are written to ~/.maily/logs/scan_errors.log

#### Scenario: Error log format
- **WHEN** writing errors to log
- **THEN** each entry includes timestamp, email ID, error type, and details
