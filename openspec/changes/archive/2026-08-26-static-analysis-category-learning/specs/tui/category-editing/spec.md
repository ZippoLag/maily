## Purpose

Provides users with an interactive interface to view and modify email categories in the TUI, enabling them to correct misclassifications and teach maily their personal patterns.

## ADDED Requirements

### Requirement: Display categories with badges

The TUI SHALL display each email's primary category prominently and SHALL show additional categories as badges on the same row.

#### Scenario: Email with single category
- **WHEN** email is classified only as "Work"
- **THEN** TUI shows "Work" as the primary category with no additional badges

#### Scenario: Email with multiple categories
- **WHEN** email is classified as ["Action Required", "Work"]
- **THEN** TUI shows one as primary (e.g., first matched) and the other as a badge

#### Scenario: Email with user override
- **WHEN** user has manually changed email categories
- **THEN** TUI displays user-assigned categories, marking them as "user-defined"

### Requirement: Category edit mode

The TUI SHALL provide a keyboard shortcut (e.g., 'c') to enter category edit mode for the selected email, allowing users to add or remove categories.

#### Scenario: Enter edit mode
- **WHEN** user presses 'c' on a selected email
- **THEN** TUI opens category edit interface for that email

#### Scenario: Toggle categories
- **WHEN** user is in category edit mode
- **THEN** user can toggle categories on/off for the selected email

#### Scenario: Save changes
- **WHEN** user confirms category changes
- **THEN** changes are persisted immediately and classification updates

### Requirement: Multi-select for batch editing

The TUI SHALL allow users to select multiple emails and apply category changes to all selected emails at once.

#### Scenario: Batch category assignment
- **WHEN** user selects 3 emails and assigns "Action Required"
- **THEN** all 3 emails have "Action Required" added to their categories

#### Scenario: Batch category removal
- **WHEN** user selects 5 emails and removes "Work"
- **THEN** "Work" is removed from all 5 emails' categories

### Requirement: Visual feedback for changes

The TUI SHALL provide immediate visual feedback when categories are changed, including highlighting modified emails and showing a confirmation message.

#### Scenario: Category added
- **WHEN** user adds "Personal" to an email
- **THEN** TUI briefly shows "Added: Personal" notification

#### Scenario: Category removed
- **WHEN** user removes "Work" from an email
- **THEN** TUI briefly shows "Removed: Work" notification

### Requirement: Keyboard-driven navigation

All category editing functionality SHALL be accessible via keyboard shortcuts without requiring mouse interaction.

#### Scenario: Keyboard-only editing
- **WHEN** user navigates with arrow keys and presses 'c'
- **THEN** category edit mode opens without mouse interaction

#### Scenario: Exit without saving
- **WHEN** user presses Escape in edit mode
- **THEN** changes are discarded and TUI returns to browse mode
