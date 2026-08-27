# tui/email-expansion Specification

## Purpose
Enables users to view email details (sender and body) by expanding email nodes in the TUI, addressing the current gap where navigating to emails does nothing.

## Requirements

### Requirement: Email expansion on selection

The TUI SHALL display the sender and body content when a user selects (expands) an email node, rendering the details in a reading pane below the category tree.

#### Scenario: User selects an email node
- **WHEN** user navigates to and selects an email in the TUI tree
- **THEN** the reading pane shows the sender email and message body

#### Scenario: Email already expanded
- **WHEN** user selects an already-expanded email
- **THEN** the pane refreshes with that email's details

### Requirement: Expansion visual indication

The TUI SHALL provide clear visual indication of which emails are expanded, using tree node expansion indicators (▼/▶ or similar).

#### Scenario: Expanded email visual
- **WHEN** an email is expanded
- **THEN** the tree node shows an expanded indicator (e.g., ▼) and the content is visible below

#### Scenario: Collapsed email visual
- **WHEN** an email is collapsed
- **THEN** the tree node shows a collapsed indicator (e.g., ▶) and only the subject is visible

### Requirement: Body content formatting

The TUI SHALL format email body content for readability, wrapping long lines to the available width of the pane and preserving the message's own paragraph structure.

#### Scenario: Long body text
- **WHEN** an email has a body longer than the pane width
- **THEN** the TUI wraps the text to the pane width and allows scrolling to view all content

#### Scenario: Body with paragraph breaks
- **WHEN** the stored body contains blank lines between paragraphs
- **THEN** the pane preserves those paragraph breaks instead of flattening them into a single line

#### Scenario: Terminal resized
- **WHEN** the user resizes the terminal while viewing an expanded body
- **THEN** the body reflows to the new available width

#### Scenario: Empty body
- **WHEN** an email has no body content
- **THEN** the TUI displays \"(no body)\" or similar indicator

### Requirement: Sender display format

The TUI SHALL display the sender information prominently when an email is expanded, showing both sender name and email address.

#### Scenario: Sender with name and email
- **WHEN** an email has both sender_name and sender_email
- **THEN** the TUI displays \"From: Name <email@example.com>\"

#### Scenario: Sender with only email
- **WHEN** an email has only sender_email
- **THEN** the TUI displays \"From: email@example.com\"

### Requirement: Keyboard navigation for expansion

The TUI SHALL support expanding and collapsing emails using standard keyboard navigation (Enter to expand, Enter again to collapse, or arrow keys).

#### Scenario: Enter key expands
- **WHEN** user presses Enter on a collapsed email
- **THEN** the email expands to show details

#### Scenario: Enter key collapses
- **WHEN** user presses Enter on an expanded email
- **THEN** the email collapses to hide details

### Requirement: Expanded email details pane

The TUI SHALL provide a dedicated reading pane below the category tree that displays the selected email's details at the current terminal width.

#### Scenario: Pane shows selected email details
- **WHEN** the user selects an email
- **THEN** the pane displays the sender, subject, and body wrapped to the pane's width

#### Scenario: Pane scrolls long bodies
- **WHEN** the wrapped body is taller than the pane
- **THEN** the pane scrolls vertically so the full body is reachable