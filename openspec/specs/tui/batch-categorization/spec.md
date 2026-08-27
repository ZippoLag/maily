# tui/batch-categorization Specification

## Purpose
Allows users to apply categories to multiple selected emails at once, enabling efficient batch categorization of backlog emails.

## Requirements

### Requirement: Batch category application

The TUI SHALL allow users to apply one or more categories to all currently selected emails with a single action.

#### Scenario: Apply category to selection
- **WHEN** user selects 5 emails and applies "Work" category
- **THEN** all 5 emails have "Work" added to their categories

#### Scenario: Apply multiple categories
- **WHEN** user selects 3 emails and applies ["Work", "Action Required"]
- **THEN** all 3 emails have both categories added

### Requirement: Batch category confirmation

The TUI SHALL show a confirmation dialog before applying categories to multiple emails, displaying the count and category names.

#### Scenario: Confirm batch categorization
- **WHEN** user attempts to apply categories to 5 selected emails
- **THEN** a dialog shows "Apply [Work] to 5 emails?" with Yes/No options

#### Scenario: Cancel batch categorization
- **WHEN** user cancels the confirmation dialog
- **THEN** no categories are applied

### Requirement: Batch category hotkey

The TUI SHALL provide a hotkey ('c') to open the category selection for batch application when emails are selected.

#### Scenario: Category hotkey with selection
- **WHEN** user has emails selected and presses 'c'
- **THEN** category selection opens for batch application

#### Scenario: Category hotkey without selection
- **WHEN** user has no emails selected and presses 'c'
- **THEN** single-email category edit opens (existing behavior)

### Requirement: Batch operation feedback

The TUI SHALL provide visual feedback when batch categorization completes, showing the count of emails affected.

#### Scenario: Success notification
- **WHEN** batch categorization completes successfully
- **THEN** a notification shows "Applied [Work] to 5 emails"

#### Scenario: Partial success
- **WHEN** batch categorization fails for some emails
- **THEN** a notification shows "Applied [Work] to 3 of 5 emails" with error details