# tui/gmail-label-badges Specification

## Purpose
Displays Gmail labels/tags/folders as visual badges on emails, helping users understand the email's Gmail organization and identify patterns for batch actions.

## Requirements

### Requirement: Gmail label exposure

The Gmail client SHALL expose label information from the Gmail API and SHALL include it in the EmailMessage model.

#### Scenario: Labels fetched from Gmail
- **WHEN** fetching an email from Gmail
- **THEN** all Gmail labels are included in the response

#### Scenario: Label data in model
- **WHEN** parsing a Gmail message
- **THEN** EmailMessage includes labels field

### Requirement: Label badge display

The TUI SHALL display Gmail labels as visual badges (colored tags) alongside each email.

#### Scenario: Single label badge
- **WHEN** an email has "Important" label
- **THEN** TUI shows [Important] badge next to the email

#### Scenario: Multiple label badges
- **WHEN** an email has "Important" and "Work" labels
- **THEN** TUI shows [Important] [Work] badges

### Requirement: Label badge styling

The TUI SHALL use consistent styling for label badges, with colors based on label type if possible.

#### Scenario: System label colors
- **WHEN** displaying system labels (Important, Starred)
- **THEN** use standard colors (yellow for Important, etc.)

#### Scenario: Custom label colors
- **WHEN** Gmail has custom label colors
- **THEN** use those colors if available, otherwise use defaults

### Requirement: Label filter by badge

The TUI SHALL allow users to filter emails by clicking on a label badge.

#### Scenario: Click label to filter
- **WHEN** user clicks [Important] badge
- **THEN** TUI filters to show only emails with Important label

#### Scenario: Click again to clear filter
- **WHEN** user clicks active label filter badge
- **THEN** filter is cleared

### Requirement: Label badge tooltip

The TUI SHALL show a tooltip with full label name on hover for truncated labels.

#### Scenario: Long label name
- **WHEN** label name is truncated in badge
- **THEN** hover shows full label name in tooltip

#### Scenario: System label description
- **WHEN** hovering over [Important]
- **THEN** tooltip shows "Marked as important by Gmail"