## ADDED Requirements

### Requirement: Graceful degradation on summary-cache failure

Summary generation SHALL degrade to a deterministic preview when the summary cache is unavailable or fails, without terminating the TUI.

#### Scenario: Summary cache cannot be read
- **WHEN** the user summarizes an email and reading the summary cache fails (for example, the cache table is missing)
- **THEN** the TUI shows the deterministic preview instead of crashing

#### Scenario: Summary cache cannot be written
- **WHEN** generating a summary and persisting it to the cache fails
- **THEN** the TUI still presents the generated summary and does not terminate
