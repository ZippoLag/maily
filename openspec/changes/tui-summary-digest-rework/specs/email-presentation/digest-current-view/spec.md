## MODIFIED Requirements

### Requirement: Digest hotkey
The TUI SHALL provide a hotkey (`D`, shift+d for digest) that generates a summary of **all emails in all categories for the current date**, regardless of whether they are marked or selected.

#### Scenario: User presses digest hotkey
- **WHEN** user presses `D` in TUI
- **THEN** a digest of all current-date emails across all categories is displayed

#### Scenario: Digest of current category
- **WHEN** the user is viewing the TUI and the current date has emails across categories
- **THEN** the digest summarizes all current-date emails in every category, not only one category's visible emails

#### Scenario: Digest ignores mark/selection state
- **WHEN** emails exist for the current date and some are neither marked nor selected
- **THEN** the digest still summarizes all of those current-date emails

### Requirement: Digest content
The digest SHALL include a formatted breakdown of totals by category and SHALL generate one paragraph per non-empty category for the current date. Category totals SHALL be rendered as a readable list rather than raw inline text.

#### Scenario: Digest includes counts
- **WHEN** generating the digest for the current date
- **THEN** the digest shows a per-category breakdown such as "Action Required: 5, Work: 10, Personal: 5"

#### Scenario: Digest includes themes
- **WHEN** generating the digest
- **THEN** the digest shows one paragraph per non-empty category covering that category's key themes and action items

#### Scenario: Empty categories are skipped
- **WHEN** generating the digest and a category has no current-date emails
- **THEN** that category is not rendered as a paragraph

#### Scenario: Digest totals as a list
- **WHEN** the digest is displayed
- **THEN** the per-category totals are formatted as a list (for example, one category per line)

### Requirement: Inference-assisted digest
When inference is enabled and available, the digest SHALL use AI to identify key information, action items, and patterns across all current-date emails.

#### Scenario: AI digest
- **WHEN** inference is enabled
- **THEN** digest includes AI-identified themes and action items across all current-date emails

#### Scenario: Fallback digest
- **WHEN** inference is unavailable
- **THEN** digest uses deterministic counting and simple pattern matching across all current-date emails