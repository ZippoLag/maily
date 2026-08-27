# gmail-account-access Specification

## Purpose
Provides privacy-conscious access to one Gmail account so maily can inspect the messages needed for the initial daily triage workflow.

## Requirements

### Requirement: Guided single-account authentication

The system SHALL guide the user through supplying a Google OAuth desktop-client JSON file and SHALL authenticate exactly one Gmail account for v1.

#### Scenario: First authentication
- **WHEN** no valid account credentials are available and the user starts a Gmail operation
- **THEN** the system explains how to obtain the OAuth file, validates the supplied file, opens the Google consent flow, and records the authenticated account identity

#### Scenario: Invalid OAuth configuration
- **WHEN** the supplied OAuth file is missing, malformed, or incompatible with the required flow
- **THEN** the system stops before contacting Gmail and reports the corrective action

### Requirement: Least-privilege read access

The system SHALL use read-only Gmail authorization for the initial scan and SHALL request broader permissions only in a later workflow that explicitly requires mutations.

#### Scenario: Read-only scan authorization
- **WHEN** the user authorizes the initial scan
- **THEN** the requested access is limited to reading Gmail data needed for synchronization

#### Scenario: Expired or revoked authorization
- **WHEN** Gmail rejects the stored authorization or reports that it has expired or been revoked
- **THEN** the system asks the user to authenticate again and does not continue with stale credentials

### Requirement: Today-focused Gmail synchronization

The system SHALL retrieve unread messages received today from the Gmail account's inbox and spam locations, using the configured local timezone to determine the day boundary.

#### Scenario: Initial daily scan
- **WHEN** the user starts a scan after authentication
- **THEN** the system retrieves only messages that are unread and whose Gmail received timestamp falls within the current local day, separating spam messages from non-spam messages

#### Scenario: Empty result
- **WHEN** no unread messages match today's inbox or spam queries
- **THEN** the system returns an explicit empty result without treating older messages as synchronized

### Requirement: Gmail failure reporting

The system SHALL report network, quota, permission, and API failures in a user-actionable way and SHALL preserve the last successful local state.

#### Scenario: Temporary Gmail outage
- **WHEN** Gmail cannot be reached during synchronization
- **THEN** the system reports that the scan is incomplete and leaves previously synchronized data unchanged