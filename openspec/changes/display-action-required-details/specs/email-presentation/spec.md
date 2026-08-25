## MODIFIED Requirements

### Requirement: Human-readable scan output

The CLI SHALL display today's scan status, category counts, classification degradation, and deferred historical counts in a human-readable format. For the "Action Required" category, the CLI SHALL additionally display the subject and sender of each email.

#### Scenario: Scan with Action Required emails
- **WHEN** the scan completes with messages in the "Action Required" category
- **THEN** the human-readable output includes the subject and sender for each "Action Required" email in addition to the category count

#### Scenario: Partial initial dataset
- **WHEN** only today's unread messages have been synchronized
- **THEN** the output labels older unread and read counts as deferred rather than displaying them as zero

#### Scenario: Scan with no Action Required emails
- **WHEN** the scan completes with no messages in the "Action Required" category
- **THEN** the human-readable output displays category counts only for "Action Required"
