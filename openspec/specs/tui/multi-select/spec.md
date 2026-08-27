# tui/multi-select Specification

## Purpose
Enables users to select multiple emails in the TUI for batch operations, addressing the need to efficiently process large email volumes.

## Requirements

### Requirement: Multi-select capability

The TUI SHALL allow users to select multiple emails simultaneously using keyboard and/or mouse.

#### Scenario: Keyboard multi-select
- **WHEN** user presses Space on an email
- **THEN** the email is toggled in the selection

#### Scenario: Mouse multi-select
- **WHEN** user Ctrl+clicks an email
- **THEN** the email is toggled in the selection

### Requirement: Visual selection indicators

The TUI SHALL clearly indicate which emails are selected, using checkboxes, highlighting, or similar visual cues.

#### Scenario: Selected email appearance
- **WHEN** an email is selected
- **THEN** it shows a checked checkbox or highlighted background

#### Scenario: Deselected email appearance
- **WHEN** an email is deselected
- **THEN** the selection indicator is removed

### Requirement: Selection count display

The TUI SHALL display the current selection count (e.g., "3 of 10 selected").

#### Scenario: Selection count in status
- **WHEN** user has selected 3 emails
- **THEN** status bar shows "3 of 10 selected"

#### Scenario: Zero selection
- **WHEN** no emails are selected
- **THEN** status bar shows "0 selected" or no selection indicator

### Requirement: Select all / Deselect all

The TUI SHALL provide keyboard shortcuts to select all or deselect all visible emails.

#### Scenario: Select all visible
- **WHEN** user presses Ctrl+A
- **THEN** all visible emails are selected

#### Scenario: Deselect all
- **WHEN** user presses Ctrl+D
- **THEN** all emails are deselected

### Requirement: Selection persists across navigation

The TUI SHALL maintain the selection set when user scrolls or changes sort order within the same view.

#### Scenario: Scroll with selection
- **WHEN** user scrolls after selecting emails
- **THEN** the selection persists on the selected emails

#### Scenario: Change sort with selection
- **WHEN** user changes sort order with emails selected
- **THEN** selection persists on the same emails (by ID)