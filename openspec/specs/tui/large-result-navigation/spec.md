# tui/large-result-navigation Specification

## Purpose
Enables the TUI to handle displaying and navigating through thousands of emails efficiently without becoming unresponsive or overwhelming the user.

## Requirements

### Requirement: Virtual scrolling

The TUI SHALL implement virtual scrolling to only render emails visible in the viewport, rather than all emails at once.

#### Scenario: 10000 emails in category
- **WHEN** a category contains 10000 emails
- **THEN** TUI only renders the ~20 visible emails, not all 10000

#### Scenario: Scroll performance
- **WHEN** user scrolls through large result set
- **THEN** scrolling is smooth with no perceptible delay

### Requirement: Lazy loading

The TUI SHALL load email details (body, sender) only when needed for display, not upfront for all emails.

#### Scenario: Expand email to load body
- **WHEN** user expands an email
- **THEN** body is loaded from database at that time

#### Scenario: Scroll to load more
- **WHEN** user scrolls near bottom of loaded results
- **THEN** system loads next batch of emails

### Requirement: Result count display

The TUI SHALL display the total count and visible range of results.

#### Scenario: Showing results 1-50 of 5000
- **WHEN** viewing first page of 5000 results
- **THEN** TUI shows \"Showing 1-50 of 5000 emails\"

#### Scenario: Filtered view count
- **WHEN** viewing filtered results
- **THEN** count reflects filtered subset

### Requirement: Keyboard navigation

The TUI SHALL support efficient keyboard navigation through large result sets.

#### Scenario: Page up/down
- **WHEN** user presses Page Up/Page Down
- **THEN** TUI scrolls by one page

#### Scenario: Jump to top/bottom
- **WHEN** user presses Home/End
- **THEN** TUI jumps to first/last email

### Requirement: Date-based grouping

The TUI SHALL group emails by date (today, yesterday, last week, older) to help users navigate large result sets.

#### Scenario: Emails grouped by date
- **WHEN** viewing a category with emails from multiple dates
- **THEN** emails are grouped under date headers like \"Today\", \"Yesterday\", \"Last Week\", \"January\"

#### Scenario: Expandable date groups
- **WHEN** user expands a date group
- **THEN** emails from that date are shown