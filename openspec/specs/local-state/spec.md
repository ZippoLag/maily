# local-state Specification

## Purpose
Maintains local configuration and synchronized email state across runs without exposing OAuth secrets in ordinary files.

## Requirements

### Requirement: Home-directory application state

The system SHALL store its configuration, database, migration state, and diagnostic logs beneath the user's `~/.maily/` directory.

#### Scenario: First launch
- **WHEN** the user launches maily without an existing state directory
- **THEN** the system creates the required directory structure with restrictive permissions and initializes default configuration

#### Scenario: Existing configuration
- **WHEN** the user launches maily with an existing configuration
- **THEN** the system loads it without overwriting user-defined values

### Requirement: Versioned SQLite persistence

The system SHALL persist message metadata, thread metadata, synchronization state, classification results, and action history in a versioned SQLite schema and SHALL apply pending migrations before using the database. Schema additions for capabilities shipped after a database's first migration SHALL be delivered as versioned migrations so every supported existing database reaches the full current schema.

#### Scenario: New database
- **WHEN** maily starts with no database
- **THEN** it creates the current schema and records the applied migration version

#### Scenario: Upgrade database
- **WHEN** the database has an older supported schema version
- **THEN** maily applies migrations in order and refuses to operate if a migration fails

#### Scenario: Existing database missing a later-added table
- **WHEN** a database was first migrated before a capability (such as email summaries) existed and is missing its table
- **THEN** running the application migrates it to the current schema, creating the missing tables and indexes while preserving existing data

### Requirement: Protected credentials

The system SHALL store OAuth tokens through the operating system credential store when available and SHALL never write access or refresh tokens to plaintext configuration, logs, or SQLite records.

#### Scenario: Token storage
- **WHEN** authentication succeeds
- **THEN** the token is stored under a maily-specific credential key and only a non-secret reference or account identity is persisted locally

#### Scenario: Unavailable credential store
- **WHEN** no supported secure credential store is available
- **THEN** the system refuses to persist tokens insecurely and explains the required user action

### Requirement: Local timezone configuration

The system SHALL store the timezone used for daily boundaries in configuration and SHALL provide a documented default based on the host environment.

#### Scenario: Date boundary
- **WHEN** a message timestamp is evaluated for \"today\"
- **THEN** the system compares it against the configured timezone's start and end of day