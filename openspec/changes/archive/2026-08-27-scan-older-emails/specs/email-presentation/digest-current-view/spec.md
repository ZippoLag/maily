## Purpose

Enables users to get a digest/summary of all currently visible emails in the TUI, providing a quick overview of the current view without needing to read each email individually.

## ADDED Requirements

### Requirement: Digest hotkey

The TUI SHALL provide a hotkey ('d' for digest) that generates a summary of all currently displayed emails.

#### Scenario: User presses digest hotkey
- **WHEN** user presses 'd' in TUI
- **THEN** a digest of visible emails is displayed

#### Scenario: Digest of current category
- **WHEN** user is viewing a category with 20 visible emails
- **THEN** digest summarizes those 20 emails

### Requirement: Digest content

The digest SHALL include a count of emails, breakdown by category (if multi-category view), and key themes/action items from the visible emails.

#### Scenario: Digest includes counts
- **WHEN** generating digest of visible emails
- **THEN** digest shows "20 emails: 5 Action Required, 10 Work, 5 Personal"

#### Scenario: Digest includes themes
- **WHEN** generating digest
- **THEN** digest shows common themes like "3 invoices, 5 newsletters, 2 meeting requests"

### Requirement: Inference-assisted digest

When inference is enabled and available, the digest SHALL use AI to identify key information, action items, and patterns across the visible emails.

#### Scenario: AI digest
- **WHEN** inference is enabled
- **THEN** digest includes AI-identified themes and action items

#### Scenario: Fallback digest
- **WHEN** inference is unavailable
- **THEN** digest uses deterministic counting and simple pattern matching

### Requirement: Digest display

The digest SHALL be displayed in a modal or dedicated pane that can be dismissed without losing the current view.

#### Scenario: Modal digest
- **WHEN** digest is generated
- **THEN** a modal shows the digest text

#### Scenario: Dismiss without losing place
- **WHEN** user dismisses digest
- **THEN** they return to the same scroll position

### Requirement: Digest caching

The system SHALL cache generated digests and SHALL reuse them if the visible emails haven't changed.

#### Scenario: Same view, cached digest
- **WHEN** user requests digest of same view
- **THEN** cached digest is displayed immediately

#### Scenario: View changed, new digest
- **WHEN** user scrolls or changes filter then requests digest
- **THEN** a new digest is generated
