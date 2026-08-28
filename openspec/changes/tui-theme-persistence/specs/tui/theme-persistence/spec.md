## Purpose

Persists the user's chosen Textual color theme so it survives application restart, instead of being reset on every launch.

## ADDED Requirements

### Requirement: Theme restoration
The TUI SHALL restore the user's last-selected color theme on startup.

#### Scenario: Theme restored on launch
- **WHEN** the TUI starts after the user previously selected a theme
- **THEN** the application opens with that same theme applied

#### Scenario: No saved theme
- **WHEN** the TUI starts and no theme has been saved
- **THEN** the application uses the default theme

### Requirement: Theme persistence on change
The TUI SHALL persist the theme when the user changes it during a session, so the new selection is available next launch.

#### Scenario: Theme change is saved
- **WHEN** the user selects a new theme
- **THEN** the selection is written to the settings and restored on the next launch

### Requirement: Documented theme setting
The persisted configuration SHALL include the theme field in its documented defaults.

#### Scenario: Default template shows theme
- **WHEN** the default settings template is written
- **THEN** it documents the theme option and its default value