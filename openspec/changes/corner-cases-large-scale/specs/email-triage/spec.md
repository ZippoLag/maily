## MODIFIED Requirements

### Requirement: Multi-category assignment

The system SHALL permit a message to belong to multiple categories and SHALL count that message in every assigned category. Additionally, the system SHALL support batch categorization of multiple messages at once.

#### Scenario: Overlapping classification
- **WHEN** a message is classified as both action-required and work-related
- **THEN** it appears in both category results and contributes one count to each category

#### Scenario: Batch categorization
- **WHEN** user applies a category to 10 selected messages
- **THEN** all 10 messages have the category added to their classification

### Requirement: Classification persistence and reruns

The system SHALL persist classification inputs and results locally and SHALL avoid repeating an unchanged inference request unless the user requests reclassification or the relevant configuration changes. For batch operations, the system SHALL efficiently handle bulk persistence.

#### Scenario: Repeated scan
- **WHEN** a synchronized message and classification configuration are unchanged
- **THEN** maily reuses the stored result and identifies it as cached

#### Scenario: Batch classification persistence
- **WHEN** batch categorization is applied to 100 messages
- **THEN** all 100 classifications are persisted efficiently in minimal transactions

#### Scenario: Configuration change
- **WHEN** a classification rule or inference configuration changes
- **THEN** maily marks affected messages for reclassification on the next applicable scan
