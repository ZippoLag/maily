## MODIFIED Requirements

### Requirement: Actions execute on focused email without explicit selection
The TUI SHALL allow actions (Summarize, Mark, Edit Categories) to execute on the currently focused email without requiring the user to first press Space or perform any other selection toggle. Marking SHALL be triggered by Enter or Space rather than the `m` key.

#### Scenario: Summarize on focused email
- **WHEN** user presses 'S' while an email is focused in the tree
- **THEN** the summary is generated and displayed for that email
- **AND** no "Select an email first" error is shown

#### Scenario: Mark on focused email
- **WHEN** user presses Enter or Space while an email is focused in the tree
- **THEN** that email is toggled in the marked set
- **AND** no "Select an email first" error is shown

#### Scenario: Edit Categories on focused email
- **WHEN** user presses 'c' while an email is focused in the tree
- **THEN** the category edit modal opens for that email
- **AND** no "Select an email first" error is shown

#### Scenario: Single-mark key removed
- **WHEN** user presses `m`
- **THEN** the system performs no action (the binding is absent)

### Requirement: Bulk actions on marked emails
The TUI SHALL apply actions to all marked emails when one or more emails are marked, rather than only the focused email.

#### Scenario: Summarize multiple marked emails
- **WHEN** user marks 3 emails and presses 'S'
- **THEN** summaries are generated for all 3 marked emails
- **AND** a combined summary is displayed

#### Scenario: Mark adds to existing marked set
- **WHEN** user marks an email while other emails are already marked
- **THEN** the newly marked email is added to the marked set
- **AND** the status bar shows the updated count of marked emails

#### Scenario: No emails marked uses focused email
- **WHEN** no emails are marked and user presses an action key
- **THEN** the action applies to the currently focused email only

## ADDED Requirements

### Requirement: Mark-all for the current date
The TUI SHALL bind `Ctrl+M` to toggle the mark state of every email in the current date (the same date scope the digest uses), regardless of which rows are visible in the current scroll.

#### Scenario: Toggle mark-all for the current date
- **WHEN** the user presses `Ctrl+M`
- **THEN** the system toggles the mark state for all emails in the current date

#### Scenario: Mark-all applies beyond the visible scroll
- **WHEN** the current date has emails outside the visible scroll region
- **THEN** `Ctrl+M` toggles those emails too

### Requirement: Unsupported modifier-key bindings removed
The TUI SHALL NOT bind Shift+arrow key combinations to any action.

#### Scenario: Shift+arrow does nothing
- **WHEN** the user presses Shift combined with an arrow key
- **THEN** the system performs no action (the binding is absent)

### Requirement: Sorting explains itself
The `s` (sort) action SHALL display a message explaining the current sorting logic before or while applying it, so the available ordering is always discoverable.

#### Scenario: Sort shows its logic
- **WHEN** the user presses `s`
- **THEN** the system shows a message describing the current sorting rule and applies the sort