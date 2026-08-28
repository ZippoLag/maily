## MODIFIED Requirements

### Requirement: Summary hotkey
The TUI SHALL provide a hotkey (`S`, shift+s) that generates and displays a summary. When one or more emails are marked, the system SHALL generate a brief paragraph per marked email. When no email is marked, the system SHALL summarize only the selected (highlighted) email. When no email is marked and no email is selected, the system SHALL NOT open a summary view and SHALL display a message explaining why it did not open.

#### Scenario: User presses summary hotkey
- **WHEN** user presses `S` with one or more emails marked
- **THEN** a summary view shows a brief paragraph for each marked email

#### Scenario: Summary hotkey on category node
- **WHEN** user presses `S` with a category (not email) selected
- **THEN** the system shows an error or no-op (no summary generated)

#### Scenario: Summary hotkey with no selection
- **WHEN** user presses `S` with no email marked and no email selected
- **THEN** the summary view does not open and the system shows a message explaining why

#### Scenario: Summarize selected fallback
- **WHEN** no email is marked but an email is highlighted and the user presses `S`
- **THEN** a summary view shows a brief paragraph for the highlighted email