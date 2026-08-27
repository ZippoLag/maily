# tui/suggestion-review Specification

## Purpose

Provides a TUI interface for reviewing and managing AI-generated suggestions for batch actions on large email sets.

## Requirements

### Requirement: Suggestion review mode

The TUI SHALL have a dedicated mode for reviewing bulk suggestions, activated when bulk suggestions are available.

#### Scenario: Enter suggestion review
- **WHEN** bulk suggestions are generated
- **THEN** TUI switches to suggestion review mode

#### Scenario: Exit suggestion review
- **WHEN** user presses Escape in suggestion review
- **THEN** TUI returns to normal browsing mode

### Requirement: Suggestion list display

The TUI SHALL display a list of suggestions with confidence indicators, affected email count, and action type.

#### Scenario: Suggestion list format
- **WHEN** displaying suggestions
- **THEN** each shows: "[High] Delete 500 emails from newsletter@example.com"

#### Scenario: Confidence indicators
- **WHEN** displaying confidence levels
- **THEN** High=green, Medium=yellow, Low=gray

### Requirement: Suggestion filtering

The TUI SHALL allow users to filter suggestions by confidence level, action type, or email count.

#### Scenario: Filter by confidence
- **WHEN** user selects "Show High Confidence Only"
- **THEN** only high-confidence suggestions are displayed

#### Scenario: Filter by action type
- **WHEN** user selects "Show Delete Suggestions Only"
- **THEN** only delete suggestions are displayed

### Requirement: Suggestion preview

The TUI SHALL allow users to preview which emails would be affected by a suggestion before accepting it.

#### Scenario: Preview affected emails
- **WHEN** user selects a suggestion
- **THEN** TUI shows list of email subjects that would be affected

#### Scenario: Preview with sampling
- **WHEN** suggestion affects 1000+ emails
- **THEN** TUI shows first 50 emails as sample with "+950 more"

### Requirement: Bulk accept/reject

The TUI SHALL allow users to accept or reject multiple suggestions at once.

#### Scenario: Accept all high confidence
- **WHEN** user selects "Accept All High Confidence"
- **THEN** all high-confidence suggestions are accepted

#### Scenario: Reject all low confidence
- **WHEN** user selects "Reject All Low Confidence"
- **THEN** all low-confidence suggestions are rejected

### Requirement: Suggestion action execution

The TUI SHALL execute categorization suggestions immediately and SHALL queue mutation suggestions for later execution.

#### Scenario: Execute categorization
- **WHEN** user accepts categorization suggestion
- **THEN** categories are applied to affected emails immediately

#### Scenario: Queue mutation
- **WHEN** user accepts delete suggestion
- **THEN** mutation intent is stored for future execution

### Requirement: Suggestion history

The TUI SHALL maintain a history of accepted suggestions and SHALL allow users to review past decisions.

#### Scenario: View suggestion history
- **WHEN** user opens suggestion history
- **THEN** TUI shows list of previously accepted suggestions with timestamps

#### Scenario: Undo suggestion
- **WHEN** user undoes a categorization suggestion
- **THEN** categories are removed from affected emails
