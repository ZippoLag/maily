## Purpose

Proposes new category names to users when they frequently assign free-form category names that don't match existing categories, addressing the original requirement: "Upon reviewing this 'Other' category contents, maily may propose the user proper names to classify them."

## ADDED Requirements

### Requirement: Track free-form category assignments

The system SHALL track when users assign category names that don't exist in the configured category list, storing these as potential new category candidates.

#### Scenario: User assigns non-existent category
- **WHEN** user assigns "Finance" to an email and "Finance" is not in config.categories
- **THEN** the system records "Finance" as a proposed category candidate

#### Scenario: Multiple emails with same proposed category
- **WHEN** user assigns "Finance" to 5 different emails
- **THEN** the system tracks the count of emails assigned to "Finance"

### Requirement: Propose new categories to user

The system SHALL suggest adding frequently-used free-form category names to the user's configuration, with a minimum threshold (default: 3 uses).

#### Scenario: Threshold met for proposal
- **WHEN** user has assigned "Finance" to 3 or more emails
- **THEN** maily suggests: "You've used 'Finance' 3 times. Add it as a category? (y/n)"

#### Scenario: Threshold not met
- **WHEN** user has assigned "Finance" to only 2 emails
- **THEN** maily does NOT suggest adding "Finance" as a category

### Requirement: User confirmation for category addition

The system SHALL require explicit user confirmation before adding a new category to the configuration, and SHALL explain the impact (new category will appear in TUI, can be used for rules, etc.).

#### Scenario: User accepts category proposal
- **WHEN** user confirms adding "Finance" as a category
- **THEN** "Finance" is added to config.toml categories list

#### Scenario: User rejects category proposal
- **WHEN** user rejects adding "Finance" as a category
- **THEN** the proposal is dismissed but continues to be tracked

### Requirement: Proposed categories persist across sessions

The system SHALL persist proposed category candidates across maily sessions, so users see accumulated suggestions.

#### Scenario: Proposals survive restart
- **WHEN** user exits and restarts maily
- **THEN** pending category proposals are still presented

#### Scenario: Proposal dismissed permanently
- **WHEN** user explicitly rejects a category proposal with "never ask again"
- **THEN** that category is removed from proposal tracking

### Requirement: Propose during "Other" category review

The system SHALL specifically prompt for category proposals when the user is reviewing emails in the "Other" category, as this is when unclassified emails are most visible.

#### Scenario: Reviewing Other category
- **WHEN** user expands the "Other" category in TUI
- **THEN** maily checks for and displays any pending category proposals

### Requirement: Proposals require no LLM

The entire category proposal system SHALL use only deterministic counting and string comparison. No LLM inference SHALL be required.

#### Scenario: Offline category proposals
- **WHEN** maily runs without internet access
- **THEN** category proposals continue to function normally
