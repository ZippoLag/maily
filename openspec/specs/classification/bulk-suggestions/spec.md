# classification/bulk-suggestions Specification

## Purpose

Provides AI-assisted suggestions for batch actions on large groups of emails, helping users identify emails that can be safely deleted, archived, or categorized together.

## Requirements

### Requirement: Bulk suggestion generation

The system SHALL analyze groups of emails and SHALL suggest batch actions (delete, archive, categorize) with confidence scores.

#### Scenario: Suggest delete for newsletter batch
- **WHEN** analyzing 500 emails from newsletter senders
- **THEN** system suggests "Delete all 500 from newsletters (confidence: high)"

#### Scenario: Suggest categorize for work emails
- **WHEN** analyzing 200 emails with work-related content
- **THEN** system suggests "Add all to Work category (confidence: medium)"

### Requirement: Suggestion grouping

The system SHALL group emails by common characteristics and SHALL generate suggestions per group, not just for the entire set.

#### Scenario: Multiple groups identified
- **WHEN** analyzing 1000 mixed emails
- **THEN** system identifies groups: "200 newsletters", "300 receipts", "500 work emails"

#### Scenario: Group-level suggestions
- **WHEN** groups are identified
- **THEN** system suggests actions per group: "Delete newsletters", "Archive receipts"

### Requirement: Confidence scoring for bulk

The system SHALL calculate confidence for bulk suggestions based on:
- Percentage of emails matching the pattern
- Strength of the pattern match
- Consistency across the group

#### Scenario: High confidence bulk suggestion
- **WHEN** 95% of emails share a strong pattern
- **THEN** confidence is high

#### Scenario: Low confidence bulk suggestion
- **WHEN** 60% of emails share a weak pattern
- **THEN** confidence is low

### Requirement: Suggestion review interface

The TUI SHALL provide an interface for reviewing bulk suggestions, allowing users to accept, reject, or modify suggestions before application.

#### Scenario: Review suggestion list
- **WHEN** bulk suggestions are generated
- **THEN** TUI shows list: "[High] Delete 500 newsletters", "[Medium] Archive 300 receipts"

#### Scenario: Accept suggestion
- **WHEN** user accepts a suggestion
- **THEN** for categorization: applied immediately; for mutations: stored as intent

### Requirement: Inference-assisted bulk analysis

When inference is enabled, the system SHALL use AI to identify semantic patterns across large email groups that deterministic methods might miss.

#### Scenario: Semantic pattern detection
- **WHEN** inference analyzes 500 emails
- **THEN** it may identify "These are all automated notifications from your monitoring system"

#### Scenario: Deterministic fallback
- **WHEN** inference is unavailable
- **THEN** system uses pattern matching: sender domains, subject keywords, existing categories

### Requirement: Suggestion storage for later action

The system SHALL store accepted suggestions that require mutations (delete, archive) for later execution when mutation support is added.

#### Scenario: Store mutation intent
- **WHEN** user accepts "Delete 500 newsletters" suggestion
- **THEN** intent is stored in database for future execution

#### Scenario: View stored intents
- **WHEN** user wants to review pending actions
- **THEN** TUI shows list of stored mutation intents

### Requirement: Bulk suggestion performance

The system SHALL generate bulk suggestions efficiently, even for large email sets (1000+), using sampling and heuristics to avoid full content analysis.

#### Scenario: Sample-based analysis
- **WHEN** analyzing 10000 emails
- **THEN** system analyzes sample (first 100) for suggestions, validates against full set

#### Scenario: Incremental suggestion generation
- **WHEN** processing large scan in batches
- **THEN** suggestions are generated incrementally per batch, aggregated at end
