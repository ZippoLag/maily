## MODIFIED Requirements

### Requirement: Versioned SQLite persistence

The system SHALL persist message metadata, thread metadata, synchronization state, classification results, and action history in a versioned SQLite schema and SHALL apply pending migrations before using the database. Additionally, the system SHALL store user category overrides and learned rule suggestions in the database.

#### Scenario: User category overrides table
- **WHEN** user changes an email's categories in the TUI
- **THEN** the override is stored in a `user_category_overrides` table with message_id, categories, and timestamp

#### Scenario: Learned rule suggestions table
- **WHEN** maily generates a rule suggestion from user corrections
- **THEN** the suggestion is stored in a `learned_rule_suggestions` table with pattern, category, confidence, and status

#### Scenario: Migration for new tables
- **WHEN** maily starts with an existing database
- **THEN** it creates new tables for overrides and suggestions if they don't exist

### Requirement: Protected credentials

The system SHALL store OAuth tokens through the operating system credential store when available and SHALL never write access or refresh tokens to plaintext configuration, logs, or SQLite records. User category overrides and rule suggestions SHALL be stored in plaintext as they contain no sensitive information.

#### Scenario: Non-sensitive data storage
- **WHEN** user category overrides are saved
- **THEN** they are stored in the SQLite database without encryption
