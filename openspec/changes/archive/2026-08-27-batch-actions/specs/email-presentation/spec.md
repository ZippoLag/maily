## MODIFIED Requirements

### Requirement: Read-only TUI browsing

The TUI SHALL allow the user to browse categories, expand and collapse their messages, inspect message details, and sort results by first-thread date, last-thread date, inferred importance or urgency, sender name, and sender domain. Additionally, the TUI SHALL support multi-select for batch operations and SHALL display Gmail labels as badges.

#### Scenario: Browse with multi-select
- **WHEN** the user opens the TUI after a scan
- **THEN** the user can select multiple emails and perform batch operations

#### Scenario: Label badges visible
- **WHEN** viewing emails in TUI
- **THEN** Gmail labels are displayed as badges on each email

#### Scenario: TUI mutation attempt
- **WHEN** the user views a message in the TUI
- **THEN** no Gmail mutation control is offered and no message state is changed by browsing
