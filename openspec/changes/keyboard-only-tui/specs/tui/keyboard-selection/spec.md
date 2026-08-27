## Purpose

Enables keyboard-only TUI operation by treating the focused/highlighted email as the implicit selection, so actions like Summarize, Mark, and Edit Categories execute on the focused email without requiring a mouse click or explicit toggle.

## ADDED Requirements

### Requirement: Focused email is implicit selection

The TUI SHALL treat the currently highlighted/focused email in the tree as the active selection for single-email actions, regardless of whether the user navigated there by mouse click or keyboard arrow keys.

#### Scenario: Keyboard navigation sets selection
- **WHEN** user navigates to an email using arrow keys (up/down) or Page Up/Page Down
- **THEN** that email becomes the active selection for subsequent actions

#### Scenario: Mouse click sets selection
- **WHEN** user clicks on an email in the tree
- **THEN** that email becomes the active selection for subsequent actions

#### Scenario: Status bar reflects focused email
- **WHEN** user navigates to a different email
- **THEN** the status bar updates to show the sender, subject, and categories of the newly focused email

### Requirement: Actions execute on focused email without explicit selection

The TUI SHALL allow actions (Summarize, Mark, Edit Categories) to execute on the currently focused email without requiring the user to first press Space or perform any other selection toggle.

#### Scenario: Summarize on focused email
- **WHEN** user presses 'S' while an email is focused in the tree
- **THEN** the summary is generated and displayed for that email
- **AND** no "Select an email first" error is shown

#### Scenario: Mark on focused email
- **WHEN** user presses 'm' while an email is focused in the tree
- **THEN** that email is toggled in the marked set
- **AND** no "Select an email first" error is shown

#### Scenario: Edit Categories on focused email
- **WHEN** user presses 'c' while an email is focused in the tree
- **THEN** the category edit modal opens for that email
- **AND** no "Select an email first" error is shown

### Requirement: Bulk actions on marked emails

The TUI SHALL apply actions to all marked emails when one or more emails are marked, rather than only the focused email.

#### Scenario: Summarize multiple marked emails
- **WHEN** user marks 3 emails and presses 'S'
- **THEN** summaries are generated for all 3 marked emails
- **AND** a digest or combined summary is displayed

#### Scenario: Mark adds to existing marked set
- **WHEN** user marks an email while other emails are already marked
- **THEN** the newly marked email is added to the marked set
- **AND** the status bar shows the updated count of marked emails

#### Scenario: No emails marked uses focused email
- **WHEN** no emails are marked and user presses an action key
- **THEN** the action applies to the currently focused email only

### Requirement: Visual indication of focused email

The TUI SHALL visually distinguish the currently focused/highlighted email from other emails in the tree.

#### Scenario: Focused email highlighting
- **WHEN** user navigates to an email
- **THEN** that email row is visually highlighted (e.g., cursor bar, different background color)

#### Scenario: Marked email indication
- **WHEN** an email is marked
- **THEN** it shows a distinct visual indicator (e.g., checkbox, prefix symbol, or different color)
