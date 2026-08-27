# tui/email-summary Specification

## Purpose
Provides users with the ability to generate and view a summary of the currently selected email via a hotkey, enabling quick understanding of email content without reading the full body.

## Requirements

### Requirement: Summary hotkey

The TUI SHALL provide a hotkey ('s') that generates and displays a summary for the currently selected email, regardless of whether it is expanded or collapsed.

#### Scenario: User presses summary hotkey
- **WHEN** user presses 's' with an email selected
- **THEN** a summary of that email is displayed

#### Scenario: Summary hotkey on category node
- **WHEN** user presses 's' with a category (not email) selected
- **THEN** the system shows an error or no-op (no summary generated)

#### Scenario: Summary hotkey with no selection
- **WHEN** user presses 's' with no email selected
- **THEN** the system shows an error or no-op

### Requirement: Summary generation

The system SHALL generate email summaries using inference when available and enabled, otherwise using a deterministic fallback (first N characters of body).

#### Scenario: Inference enabled and available
- **WHEN** inference is enabled and Ollama is available
- **THEN** the summary is generated using the inference provider

#### Scenario: Inference disabled
- **WHEN** inference is disabled
- **THEN** the summary is a deterministic truncation of the email body (first 200 characters)

#### Scenario: Inference unavailable
- **WHEN** inference is enabled but Ollama is unavailable
- **THEN** the summary falls back to deterministic truncation with a degraded indicator

### Requirement: Summary display

The TUI SHALL display the summary in a modal or popup that can be dismissed, without navigating away from the current selection.

#### Scenario: Summary modal appears
- **WHEN** summary is generated
- **THEN** a modal window displays the summary text

#### Scenario: Modal can be dismissed
- **WHEN** user presses Escape or clicks outside the modal
- **THEN** the modal closes and user returns to email browsing

#### Scenario: Summary persists across sessions
- **WHEN** a summary is generated for an email
- **THEN** the summary is cached and reused on subsequent selections (same email)

### Requirement: Summary content

The summary SHALL capture the key information from the email, including purpose, action items, and important details when generated via inference.

#### Scenario: Inference-generated summary
- **WHEN** inference generates a summary
- **THEN** the summary includes key points, action items, and sender intent

#### Scenario: Deterministic summary
- **WHEN** using fallback summary
- **THEN** the summary is clearly labeled as \"Preview\" or \"First 200 characters\"

### Requirement: Summary hotkey indication

The TUI SHALL display the summary hotkey ('s') in the footer or help text so users know it's available.

#### Scenario: Hotkey in footer
- **WHEN** TUI is open
- **THEN** the footer shows \"s: summarize\" as an available action

#### Scenario: Help text includes summary
- **WHEN** user views help
- **THEN** the summary hotkey and its purpose are documented

### Requirement: Graceful degradation on summary-cache failure

Summary generation SHALL degrade to a deterministic preview when the summary cache is unavailable or fails, without terminating the TUI.

#### Scenario: Summary cache cannot be read
- **WHEN** the user summarizes an email and reading the summary cache fails (for example, the cache table is missing)
- **THEN** the TUI shows the deterministic preview instead of crashing

#### Scenario: Summary cache cannot be written
- **WHEN** generating a summary and persisting it to the cache fails
- **THEN** the TUI still presents the generated summary and does not terminate