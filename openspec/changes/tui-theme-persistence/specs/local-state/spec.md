## ADDED Requirements

### Requirement: Runtime theme persistence
The persisted configuration SHALL include the TUI color theme selection, with a documented default. The system SHALL store the theme under the maily settings so it can be restored on later launches.

#### Scenario: Theme stored with defaults
- **WHEN** the default settings are written
- **THEN** the theme field is present with a documented default

#### Scenario: Existing configuration retains theme
- **WHEN** the user has an existing configuration and launches the TUI with a saved theme
- **THEN** the TUI loads the saved theme and does not overwrite it