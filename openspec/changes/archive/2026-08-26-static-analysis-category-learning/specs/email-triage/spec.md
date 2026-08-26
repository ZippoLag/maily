## MODIFIED Requirements

### Requirement: Configurable deterministic classification

The system SHALL allow category rules to be configured and SHALL evaluate deterministic rules before invoking an inference provider. Rules SHALL be loadable from user configuration in addition to default rules, and the system SHALL track which specific rules matched each email.

#### Scenario: Rule match with tracking
- **WHEN** a message satisfies a configured deterministic rule
- **THEN** the system assigns the rule's category and records which rule pattern matched

#### Scenario: Multiple rules match same email
- **WHEN** a message satisfies multiple deterministic rules
- **THEN** the system assigns all matching categories and records all matched rules

#### Scenario: User rule combined with default rules
- **WHEN** user defines rules in config.toml
- **THEN** the system combines user rules with default rules and applies all during classification

### Requirement: Classification persistence and reruns

The system SHALL persist classification inputs and results locally and SHALL avoid repeating an unchanged inference request unless the user requests reclassification or the relevant configuration changes. Additionally, the system SHALL store user category overrides separately and apply them after rule-based classification.

#### Scenario: User override applied after rules
- **WHEN** a message has user-assigned categories and matches deterministic rules
- **THEN** user categories are applied and rule-based categories that conflict are removed

#### Scenario: Configuration change includes rule changes
- **WHEN** user adds or modifies rules in config.toml
- **THEN** maily marks affected messages for reclassification on the next scan
