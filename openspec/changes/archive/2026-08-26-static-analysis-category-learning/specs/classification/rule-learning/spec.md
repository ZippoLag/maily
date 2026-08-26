## Purpose

Enables maily to learn and suggest new classification rules based on user category corrections, allowing the system to improve its static analysis accuracy over time without requiring LLM inference.

## ADDED Requirements

### Requirement: Track user category overrides

The system SHALL persist user category edits as overrides in the database, separate from the original classification results.

#### Scenario: User changes email category
- **WHEN** user changes an email from "Work" to "Personal" in the TUI
- **THEN** the override is stored with the message ID and new category set

#### Scenario: Override persists across scans
- **WHEN** maily performs a new scan
- **THEN** previously overridden emails retain their user-assigned categories

### Requirement: Suggest rules from user corrections

The system SHALL analyze user category overrides and SHALL suggest new rule patterns based on common keywords in reclassified emails. Suggestions SHALL be deterministic and based solely on string pattern frequency.

#### Scenario: Multiple emails corrected to same category
- **WHEN** user reclassifies 5 emails containing "newsletter" from Other to Newsletters - technical
- **THEN** maily suggests adding "newsletter" to Newsletters - technical rules

#### Scenario: Pattern extraction from email content
- **WHEN** user reclassifies emails with "team meeting" to Work
- **THEN** maily suggests patterns based on frequent words in subject/body of those emails

#### Scenario: Minimum threshold for suggestions
- **WHEN** user reclassifies only 1 email to a category
- **THEN** maily does NOT suggest a new rule (threshold not met)

### Requirement: Rule suggestion confirmation

The system SHALL present rule suggestions to the user and SHALL require explicit confirmation before adding them to the user's configuration. Suggestions SHALL be stored separately from active rules until confirmed.

#### Scenario: User reviews and accepts suggestion
- **WHEN** maily suggests rule `Action Required: ["overdue"]`
- **THEN** user can accept, reject, or edit the suggestion

#### Scenario: Suggestions persist across sessions
- **WHEN** user exits maily with pending suggestions
- **THEN** suggestions are stored and presented again on next launch

### Requirement: Filter stop words from suggestions

The system SHALL exclude common stop words (the, a, an, in, on, etc.) from rule suggestions to focus on meaningful patterns.

#### Scenario: Stop words excluded
- **WHEN** user reclassifies emails with subject "The invoice is overdue"
- **THEN** suggestion focuses on "invoice" and "overdue", not "the", "is"

### Requirement: Rule learning requires no LLM

The entire rule learning process SHALL use only deterministic string analysis. No LLM inference SHALL be required for analyzing user corrections and suggesting new patterns.

#### Scenario: Offline rule learning
- **WHEN** maily runs without internet access or Ollama
- **THEN** rule learning continues to function normally

#### Scenario: No inference dependency
- **WHEN** user has inference disabled
- **THEN** rule learning still suggests patterns based on user corrections
