## ADDED Requirements

### Requirement: Label-filter key removed
The system SHALL NOT bind the `l` key to filter by label, and SHALL NOT expose label filtering as an action. Any non-functional label-filter handler SHALL be removed.

#### Scenario: Label-filter key is unbound
- **WHEN** the user presses `l` in the TUI
- **THEN** the system performs no action (the binding is absent)

#### Scenario: No label-filter action documented
- **WHEN** the user views help or shortcuts
- **THEN** label filtering is not listed as an available action