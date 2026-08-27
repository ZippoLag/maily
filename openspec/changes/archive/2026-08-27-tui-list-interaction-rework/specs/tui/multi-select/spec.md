## MODIFIED Requirements

### Requirement: Multi-select capability
The TUI SHALL allow users to mark multiple emails simultaneously. Marking (toggling the check box) SHALL be the mechanism for including emails in batch operations.

#### Scenario: Keyboard multi-select
- **WHEN** user presses Space (or Enter) on an email
- **THEN** the email is toggled in the mark

#### Scenario: Mouse multi-select
- **WHEN** user Ctrl+clicks an email
- **THEN** the email is toggled in the mark

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

## ADDED Requirements

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