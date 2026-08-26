## Purpose

Enables users to view email details (sender and body) by expanding email nodes in the TUI, addressing the current gap where navigating to emails does nothing.

## ADDED Requirements

### Requirement: Email expansion on selection

The TUI SHALL display the sender and body content when a user selects (expands) an email node in the category tree.

#### Scenario: User selects an email node
- **WHEN** user navigates to and selects an email in the TUI tree
- **THEN** the email node expands to show sender email and message body

#### Scenario: Email already expanded
- **WHEN** user selects an already-expanded email
- **THEN** the email node collapses to show only the subject line

### Requirement: Expansion visual indication

The TUI SHALL provide clear visual indication of which emails are expanded, using tree node expansion indicators (▼/▶ or similar).

#### Scenario: Expanded email visual
- **WHEN** an email is expanded
- **THEN** the tree node shows an expanded indicator (e.g., ▼) and the content is visible below

#### Scenario: Collapsed email visual
- **WHEN** an email is collapsed
- **THEN** the tree node shows a collapsed indicator (e.g., ▶) and only the subject is visible

### Requirement: Body content formatting

The TUI SHALL format email body content for readability, including line wrapping and handling of long lines.

#### Scenario: Long body text
- **WHEN** an email has a body longer than the terminal width
- **THEN** the TUI wraps the text and allows scrolling to view all content

#### Scenario: Empty body
- **WHEN** an email has no body content
- **THEN** the TUI displays "(no body)" or similar indicator

### Requirement: Sender display format

The TUI SHALL display the sender information prominently when an email is expanded, showing both sender name and email address.

#### Scenario: Sender with name and email
- **WHEN** an email has both sender_name and sender_email
- **THEN** the TUI displays "From: Name <email@example.com>"

#### Scenario: Sender with only email
- **WHEN** an email has only sender_email
- **THEN** the TUI displays "From: email@example.com"

### Requirement: Keyboard navigation for expansion

The TUI SHALL support expanding and collapsing emails using standard keyboard navigation (Enter to expand, Enter again to collapse, or arrow keys).

#### Scenario: Enter key expands
- **WHEN** user presses Enter on a collapsed email
- **THEN** the email expands to show details

#### Scenario: Enter key collapses
- **WHEN** user presses Enter on an expanded email
- **THEN** the email collapses to hide details
