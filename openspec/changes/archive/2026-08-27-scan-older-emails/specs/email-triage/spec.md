## MODIFIED Requirements

### Requirement: Today-focused Gmail synchronization

The system SHALL retrieve unread messages received today from the Gmail account's inbox and spam locations, using the configured local timezone to determine the day boundary. Additionally, the system SHALL support retrieving messages from any historical date range when configured to do so.

#### Scenario: Initial daily scan
- **WHEN** the user starts a scan after authentication
- **THEN** the system retrieves only messages that are unread and whose Gmail received timestamp falls within the current local day, separating spam messages from non-spam messages

#### Scenario: Historical scan
- **WHEN** user configures a date range extending beyond today
- **THEN** the system retrieves messages from the specified historical range

#### Scenario: Include read emails
- **WHEN** user enables include_read configuration
- **THEN** the system retrieves both read and unread messages from the specified date range

#### Scenario: Empty result
- **WHEN** no unread messages match today's inbox or spam queries
- **THEN** the system returns an explicit empty result without treating older messages as synchronized
