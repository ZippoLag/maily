## MODIFIED Requirements

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
