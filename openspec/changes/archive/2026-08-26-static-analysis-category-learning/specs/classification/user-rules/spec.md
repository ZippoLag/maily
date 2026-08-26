## Purpose

Enables users to define custom static analysis rules in their configuration file using the same format as default rules, allowing maily to categorize emails based on personal patterns without requiring inference.

## ADDED Requirements

### Requirement: User-configurable rules in config.toml

The system SHALL allow users to define static analysis rules in their `config.toml` file. User-defined rules SHALL use the same matching semantics as default rules and SHALL be combined with default rules during classification.

#### Scenario: User adds custom rule for Personal category
- **WHEN** user adds `[classification.rules.Personal] = ["mom", "dad", "family"]` to config.toml
- **THEN** emails matching those patterns are classified as Personal

#### Scenario: User rule overrides default rule
- **WHEN** user defines a rule for a category that also has default rules
- **THEN** both default and user rules are applied (union of patterns)

#### Scenario: User removes default rule category
- **WHEN** user sets rules for a category to empty list
- **THEN** only default rules (if any) apply for that category

### Requirement: Rule format matches default rules

The system SHALL accept user rules in a format that mirrors the default rule structure: a list of regex patterns that are matched case-insensitively against message fields.

#### Scenario: Case-insensitive pattern matching
- **WHEN** user defines rule `["Urgent", "Important"]` for Action Required
- **THEN** emails with subject "URGENT: Action needed" match the rule

#### Scenario: Regex pattern support
- **WHEN** user defines rule `["invoice-.*", "payment due"]` for Action Required
- **THEN** emails with subject "invoice-2024-001" match the first pattern

### Requirement: Rule validation on config load

The system SHALL validate user-defined rules on configuration load and SHALL report syntax errors with clear messages.

#### Scenario: Invalid regex pattern
- **WHEN** user defines rule `["[invalid"]` (unclosed bracket)
- **THEN** maily reports configuration error with pattern and line number

#### Scenario: Valid configuration loads successfully
- **WHEN** user defines valid rules in config.toml
- **THEN** maily starts normally and uses the combined rule set

### Requirement: Rule precedence - user rules take priority

When the same pattern exists in both default and user rules, the user's rule SHALL take precedence for determining which category the pattern belongs to, preventing conflicts.

#### Scenario: User customizes Action Required patterns
- **WHEN** user defines Action Required rule that removes "verify" pattern
- **THEN** emails with "verify" are not classified as Action Required by default rule
