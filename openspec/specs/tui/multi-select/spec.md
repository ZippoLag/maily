# tui/multi-select Specification

## Purpose
Enables users to select multiple emails in the TUI for batch operations, addressing the need to efficiently process large email volumes.

## Requirements

### Requirement: Multi-select capability

The TUI SHALL allow users to mark multiple emails simultaneously. Marking (toggling the check box) SHALL be the mechanism for including emails in batch operations.

#### Scenario: Keyboard multi-select
- **WHEN** user presses Space (or Enter) on an email
- **THEN** the email is toggled in the mark

#### Scenario: Mouse multi-select
- **WHEN** user Ctrl+clicks an email
- **THEN** the email is toggled in the mark

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

The TUI SHALL provide a keyboard shortcut to toggle the mark state of all emails in the current date (the same date scope the digest uses). The TUI SHALL NOT bind `Ctrl+A` (select all visible) or `Ctrl+D` (deselect all).

#### Scenario: Select all visible
- **WHEN** user presses `Ctrl+M`
- **THEN** all current-date emails are toggled in the marked set, regardless of scroll position

#### Scenario: Deselect all
- **WHEN** user presses `Ctrl+M` while all current-date emails are already marked
- **THEN** all current-date emails are toggled off the marked set

#### Scenario: Select-all removed
- **WHEN** user presses `Ctrl+A`
- **THEN** the system performs no action (the binding is absent)

#### Scenario: Deselect-all key removed
- **WHEN** user presses `Ctrl+D`
- **THEN** the system performs no action (the binding is absent)

### Requirement: Selection and marking are distinct

"Selection" SHALL mean the currently highlighted email — the one row the cursor sits on. "Marking" SHALL mean the set of emails that have the check box applied. The system MUST keep these two concepts distinct in its UI and behavior.

#### Scenario: Highlight vs mark are separate
- **WHEN** the user highlights an email (moves the cursor over it)
- **THEN** that email becomes the "selection" but its check box is unchanged
- **AND WHEN** the user presses a mark toggle
- **THEN** the check box changes state while the highlighted email (selection) may be different

### Requirement: Edit categories fallback logic

The `c` (edit categories) action SHALL apply to the marked emails; if none are marked, it SHALL apply to the selected (highlighted) email; if there is no selection, it SHALL do nothing. This matches the same fallback logic `S` uses.

#### Scenario: Edit categories with marked emails
- **WHEN** one or more emails are marked and the user presses `c`
- **THEN** the system opens the category editor for the marked emails

#### Scenario: Edit categories fallback to selection
- **WHEN** no emails are marked but one email is highlighted and the user presses `c`
- **THEN** the system opens the category editor for the highlighted email

#### Scenario: Edit categories with no target
- **WHEN** no emails are marked and no email is highlighted and the user presses `c`
- **THEN** the system performs no action

### Requirement: Selection persists across navigation

The TUI SHALL maintain the selection set when user scrolls or changes sort order within the same view.

#### Scenario: Scroll with selection
- **WHEN** user scrolls after selecting emails
- **THEN** the selection persists on the selected emails

#### Scenario: Change sort with selection
- **WHEN** user changes sort order with emails selected
- **THEN** selection persists on the same emails (by ID)