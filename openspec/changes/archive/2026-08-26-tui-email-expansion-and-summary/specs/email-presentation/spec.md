## MODIFIED Requirements

### Requirement: Read-only TUI browsing

The TUI SHALL allow the user to browse categories, expand and collapse their messages, inspect message details, and sort results by first-thread date, last-thread date, inferred importance or urgency, sender name, and sender domain. Additionally, the TUI SHALL support expanding individual emails to view sender and body content, and SHALL provide a summary hotkey for selected emails.

#### Scenario: Browse and expand emails
- **WHEN** the user selects an email in the TUI
- **THEN** the email expands to show sender and body content

#### Scenario: Browse and sort
- **WHEN** the user opens the TUI after a scan
- **THEN** the user can expand a category, expand individual emails, and change sort criteria

#### Scenario: TUI mutation attempt
- **WHEN** the user views a message in the TUI
- **THEN** no Gmail mutation control is offered and no message state is changed by browsing or expanding
