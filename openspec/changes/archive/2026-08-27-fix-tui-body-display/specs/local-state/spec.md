## ADDED Requirements

### Requirement: Categorized message queries include body content

The categorized-messages query SHALL include each message's stored body content so the TUI and digest render the actual message text.

#### Scenario: Email with body renders its content
- **WHEN** the TUI renders an email whose stored message has a body
- **THEN** the email node displays the actual body text rather than "(no body)"

#### Scenario: Email without body shows placeholder
- **WHEN** the TUI renders an email whose stored message has no body content
- **THEN** the email node displays "(no body)"
