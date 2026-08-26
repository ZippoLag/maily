## Purpose

Extends Gmail synchronization beyond today's unread emails to handle any historical date range, enabling users to triage backlog emails.

## ADDED Requirements

### Requirement: Historical date range queries

The Gmail client SHALL support fetching emails from any date range, not limited to today, including specific date ranges, relative periods (last N days/weeks/months), and custom start/end dates.

#### Scenario: Scan last 7 days
- **WHEN** user requests scan of last 7 days
- **THEN** Gmail client retrieves unread emails from the past week

#### Scenario: Scan specific month
- **WHEN** user requests scan of January 2024
- **THEN** Gmail client retrieves emails from that month

#### Scenario: Scan all historical emails
- **WHEN** user requests full historical scan
- **THEN** Gmail client retrieves all emails from the account's beginning

### Requirement: Include read emails

The Gmail client SHALL support fetching both read and unread emails when requested, with a configuration option to control this behavior.

#### Scenario: Scan includes read emails
- **WHEN** user enables include_read option
- **THEN** Gmail client retrieves both read and unread emails

#### Scenario: Default excludes read emails
- **WHEN** include_read is not specified
- **THEN** Gmail client only retrieves unread emails (current behavior)

### Requirement: Date-based pagination

The Gmail client SHALL process historical emails in date-based chunks (day, week, month, year) to provide progress feedback and avoid memory issues.

#### Scenario: Process by day
- **WHEN** processing a 30-day range with day chunking
- **THEN** system processes one day at a time, reporting progress

#### Scenario: Process by week
- **WHEN** processing a year with week chunking
- **THEN** system processes one week at a time

### Requirement: Rate limit awareness

The Gmail client SHALL respect Gmail API rate limits and SHALL implement backoff/retry logic when limits are hit.

#### Scenario: Rate limit exceeded
- **WHEN** Gmail API returns rate limit error
- **THEN** system pauses and retries after appropriate delay

#### Scenario: Quota exceeded
- **WHEN** Gmail API returns quota exceeded error
- **THEN** system reports error and stops gracefully
