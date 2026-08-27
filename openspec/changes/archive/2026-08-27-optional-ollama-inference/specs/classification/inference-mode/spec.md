## Purpose

Controls when the system invokes local inference for message classification, making it opt-in rather than automatic fallback to avoid unnecessary computational overhead.

## ADDED Requirements

### Requirement: Inference mode configuration

The system SHALL provide a configuration option to control inference usage, with at least two modes: enabled and disabled. When disabled, inference SHALL NOT be invoked automatically.

#### Scenario: Inference disabled in configuration
- **WHEN** the user sets inference mode to disabled
- **THEN** the system never invokes the inference provider, even when available

#### Scenario: Inference enabled in configuration
- **WHEN** the user sets inference mode to enabled
- **THEN** the system may invoke the inference provider when deterministic rules cannot classify a message

### Requirement: Default inference mode

The system SHALL default inference mode to disabled to minimize resource usage and latency.

#### Scenario: Fresh installation
- **WHEN** maily is installed and initialized for the first time
- **THEN** inference mode defaults to disabled

### Requirement: Inference mode persists across restarts

The system SHALL persist the inference mode configuration and restore it on subsequent launches.

#### Scenario: Configuration persistence
- **WHEN** the user changes inference mode and restarts maily
- **THEN** the configured inference mode remains in effect
