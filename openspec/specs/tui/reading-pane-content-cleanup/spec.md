# tui-reading-pane-content-cleanup Specification

## Purpose

Ensures the reading pane renders clean, readable text from email bodies instead of raw HTML markup, so users can read messages without visual noise.

## Requirements

### Requirement: Convert HTML bodies to Markdown
The reading pane SHALL convert HTML email body content to Markdown/plain text before display. The system SHALL detect HTML content and apply conversion; non-HTML (plain text) bodies SHALL pass through unchanged.

#### Scenario: HTML body converted
- **WHEN** a message body contains HTML tags
- **THEN** the reading pane displays the converted clean text, not the raw HTML markup

#### Scenario: Plain-text body unchanged
- **WHEN** a message body is plain text with no HTML
- **THEN** the reading pane displays the body as-is

### Requirement: Graceful fallback on conversion failure
The reading pane SHALL NOT show raw HTML when conversion fails. If HTML conversion is not available or errors, the system SHALL fall back to a sanitized plain-text representation or the raw body, but SHALL NOT crash the TUI.

#### Scenario: Converter unavailable
- **WHEN** the HTML converter cannot be loaded
- **THEN** the reading pane shows a best-effort plain-text fallback and the TUI continues running

#### Scenario: Body absent or empty
- **WHEN** a message has no body
- **THEN** the reading pane shows a "(no body)" indicator, as currently expected