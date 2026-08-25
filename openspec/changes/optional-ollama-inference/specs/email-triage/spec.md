## MODIFIED Requirements

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
