## Purpose

Provides AI-assisted suggestions for batch actions (delete, archive, categorize) based on the currently selected emails, helping users efficiently triage large backlogs.

## ADDED Requirements

### Requirement: Batch action suggestion generation

The system SHALL analyze selected emails and SHALL suggest batch actions that could be applied to all of them, with a confidence score for each suggestion.

#### Scenario: Suggest delete for newsletters
- **WHEN** user selects 50 emails from "newsletter@example.com"
- **THEN** system suggests "Delete all 50 (confidence: high)"

#### Scenario: Suggest categorize for work emails
- **WHEN** user selects 20 emails with "meeting" in subject
- **THEN** system suggests "Add to Work category (confidence: medium)"

### Requirement: Suggestion types

The system SHALL support suggesting the following action types:
- Delete
- Archive
- Add category
- Remove category
- Mark as read (future, when mutations supported)

#### Scenario: Multiple suggestion types
- **WHEN** user selects diverse emails
- **THEN** system may suggest multiple action types with different confidence

#### Scenario: Low confidence suggestion
- **WHEN** emails don't have clear common patterns
- **THEN** system suggests with low confidence or no suggestion

### Requirement: Suggestion confidence levels

Suggestions SHALL have confidence levels: low, medium, high, based on the strength of the pattern match.

#### Scenario: High confidence
- **WHEN** all selected emails share a clear pattern (same sender, same subject prefix)
- **THEN** confidence is high

#### Scenario: Medium confidence
- **WHEN** most selected emails share a pattern
- **THEN** confidence is medium

### Requirement: Suggestion display

The TUI SHALL display suggestions in a panel with confidence indicators and action buttons.

#### Scenario: Suggestion panel
- **WHEN** user has selected emails
- **THEN** TUI shows "Suggestions: [Delete - High] [Add Work - Medium]"

#### Scenario: Accept suggestion
- **WHEN** user clicks a suggestion
- **THEN** the corresponding action is prepared for confirmation

### Requirement: Suggestion requires confirmation

The system SHALL require explicit user confirmation before executing any suggested batch action, even though the action itself (categorization) is read-only.

#### Scenario: Confirm before applying suggestion
- **WHEN** user accepts a "Delete" suggestion
- **THEN** system shows "This would delete 50 emails. Confirm?" (note: actual delete not yet implemented)

#### Scenario: Suggestion is just a suggestion
- **WHEN** user accepts a suggestion
- **THEN** for categorization: applied immediately; for mutations: stored as intent for future

### Requirement: Inference-assisted suggestions

When inference is enabled and available, the system SHALL use AI to generate more nuanced suggestions based on email content analysis.

#### Scenario: AI suggestions
- **WHEN** inference is enabled
- **THEN** suggestions may include semantic patterns ("These are all receipts")

#### Scenario: Fallback suggestions
- **WHEN** inference is unavailable
- **THEN** system uses deterministic pattern matching only

### Requirement: Suggestion caching

The system SHALL cache suggestions for a given selection set to avoid recomputing on every change.

#### Scenario: Same selection, cached suggestion
- **WHEN** user reselects the same emails
- **THEN** suggestions appear immediately from cache

#### Scenario: Selection changed, new suggestions
- **WHEN** user changes the selection
- **THEN** new suggestions are generated
