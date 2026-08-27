# email-triage Specification

## Purpose
Classifies the initial set of synchronized messages into user-facing categories while keeping deterministic behavior available when local inference is unavailable.

## Requirements

### Requirement: Required categories

The system SHALL always provide the categories `Action Required`, `Personal`, `Work`, `Work proposals`, `Job search`, `Newsletters - technical`, `Newsletters - other`, and `Other`.

#### Scenario: Default category set
- **WHEN** maily initializes classification configuration
- **THEN** all required categories are present even when no messages match them

### Requirement: Configurable deterministic classification

The system SHALL allow category rules to be configured and SHALL evaluate deterministic rules before invoking an inference provider. When deterministic rules cannot classify a message, the system SHALL only pass the message to the configured inference provider if inference mode is enabled. If inference mode is disabled, the system SHALL classify the message as `Other` without invoking the provider.

#### Scenario: Rule match with inference disabled
- **WHEN** a message satisfies a configured deterministic rule AND inference mode is disabled
- **THEN** the system assigns the rule's category without requiring an inference request

#### Scenario: No rule match with inference disabled
- **WHEN** deterministic rules cannot classify a message AND inference mode is disabled
- **THEN** the system assigns the message to `Other` without invoking the inference provider

#### Scenario: No rule match with inference enabled
- **WHEN** deterministic rules cannot classify a message AND inference mode is enabled AND the inference provider is available
- **THEN** the system passes the message to the configured inference provider

### Requirement: Local inference and fallback

The system SHALL default to local Ollama using the configured `gemma4:e2b` model, SHALL report provider failures, and SHALL classify unresolved messages as `Other` when the provider is absent, unreachable, or times out.

#### Scenario: Ollama classification succeeds
- **WHEN** Ollama responds with valid category results
- **THEN** maily stores and exposes those results with their inference status

#### Scenario: Ollama unavailable
- **WHEN** Ollama or the configured model cannot be reached within the configured timeout
- **THEN** maily reports degraded classification, retains deterministic results, and assigns unresolved messages to `Other`

### Requirement: Multi-category assignment

The system SHALL permit a message to belong to multiple categories and SHALL count that message in every assigned category.

#### Scenario: Overlapping classification
- **WHEN** a message is classified as both action-required and work-related
- **THEN** it appears in both category results and contributes one count to each category

### Requirement: Classification persistence and reruns

The system SHALL persist classification inputs and results locally and SHALL avoid repeating an unchanged inference request unless the user requests reclassification or the relevant configuration changes.

#### Scenario: Repeated scan
- **WHEN** a synchronized message and classification configuration are unchanged
- **THEN** maily reuses the stored result and identifies it as cached

#### Scenario: Configuration change
- **WHEN** a classification rule or inference configuration changes
- **THEN** maily marks affected messages for reclassification on the next applicable scan