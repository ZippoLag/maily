## Purpose

Respects Gmail API rate limits and handles quota constraints gracefully during large scan operations.

## ADDED Requirements

### Requirement: Rate limit detection

The system SHALL detect when Gmail API rate limits are being approached or exceeded.

#### Scenario: Detect rate limit error
- **WHEN** Gmail API returns 429 or rate limit error
- **THEN** system detects and classifies it as rate limit error

#### Scenario: Detect quota exceeded
- **WHEN** Gmail API returns quotaExceeded error
- **THEN** system detects and classifies it as quota error

### Requirement: Exponential backoff

The system SHALL implement exponential backoff when rate limits are hit, with jitter to avoid thundering herd.

#### Scenario: First retry after 1 second
- **WHEN** first rate limit error occurs
- **THEN** system waits ~1 second before retry

#### Scenario: Second retry after 4 seconds
- **WHEN** second rate limit error occurs
- **THEN** system waits ~4 seconds before retry

#### Scenario: Max backoff limit
- **WHEN** backoff exceeds maximum (default: 60 seconds)
- **THEN** system waits maximum time, does not exceed it

### Requirement: Jitter for backoff

The system SHALL add random jitter to backoff times to prevent synchronized retries from multiple instances.

#### Scenario: Random jitter added
- **WHEN** calculating backoff time
- **THEN** a random factor is added (e.g., ±20%)

#### Scenario: Jitter prevents thundering herd
- **WHEN** multiple instances retry simultaneously
- **THEN** random jitter staggers the retries

### Requirement: Quota usage tracking

The system SHALL track Gmail API quota usage during scans and SHALL estimate remaining quota.

#### Scenario: Track requests made
- **WHEN** making Gmail API requests
- **THEN** system counts requests per quota period

#### Scenario: Estimate remaining quota
- **WHEN** approaching quota limit
- **THEN** system estimates remaining requests and time until reset

### Requirement: Pause and resume on quota exhaustion

The system SHALL pause processing when quota is exhausted and SHALL automatically resume when quota resets.

#### Scenario: Pause on quota exhausted
- **WHEN** Gmail quota is exhausted
- **THEN** system pauses, saves state, and reports estimated wait time

#### Scenario: Auto-resume on quota reset
- **WHEN** quota resets while system is paused
- **THEN** system automatically resumes processing

#### Scenario: Manual resume option
- **WHEN** user wants to resume before quota reset
- **THEN** user can manually trigger resume attempt

### Requirement: Quota configuration

Users SHALL be able to configure quota limits and backoff parameters.

#### Scenario: Custom backoff settings
- **WHEN** user configures max_backoff_seconds = 120
- **THEN** system uses 120 seconds as maximum backoff

#### Scenario: Custom quota limit
- **WHEN** user configures daily_quota = 10000
- **THEN** system tracks against 10000 daily quota

### Requirement: Quota error reporting

The system SHALL provide clear error messages when quota issues prevent scan completion.

#### Scenario: Quota exhausted message
- **WHEN** quota is exhausted
- **THEN** system reports: "Gmail quota exhausted. 0/10000 requests remaining. Resume in ~2 hours."

#### Scenario: Rate limit message
- **WHEN** rate limited
- **THEN** system reports: "Rate limited. Retrying in 5 seconds..."
