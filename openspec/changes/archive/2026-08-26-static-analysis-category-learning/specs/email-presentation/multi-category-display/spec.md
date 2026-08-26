## Purpose

Enhances the email display to show all categories an email belongs to, with clear visual distinction between primary and secondary categories, improving user understanding of how emails are classified.

## ADDED Requirements

### Requirement: Primary and secondary category display

The system SHALL designate one category as primary and SHALL display additional categories as secondary indicators (badges, tags, etc.) for each email.

#### Scenario: Email with one category
- **WHEN** email belongs only to "Work"
- **THEN** "Work" is displayed as the primary category with no secondary badges

#### Scenario: Email with multiple categories
- **WHEN** email belongs to ["Action Required", "Work"]
- **THEN** one category is primary and the other is shown as a secondary badge

#### Scenario: More than two categories
- **WHEN** email belongs to ["Action Required", "Work", "Personal"]
- **THEN** one is primary and the remaining are shown as secondary badges

### Requirement: Primary category selection rule

The system SHALL use a deterministic rule to select the primary category. The rule SHALL be: first matched rule in priority order, or if user has overridden, use the first user-assigned category.

#### Scenario: Rule-based primary selection
- **WHEN** email matches "Action Required" rule before "Work" rule
- **THEN** "Action Required" is the primary category

#### Scenario: User override takes priority
- **WHEN** user has manually assigned categories to an email
- **THEN** the first user-assigned category is the primary category

### Requirement: Visual distinction between primary and secondary

The system SHALL visually distinguish primary categories from secondary badges using different styling (color, position, size, etc.) to make the hierarchy clear.

#### Scenario: Color differentiation
- **WHEN** displaying email categories
- **THEN** primary category uses primary color, secondary badges use secondary color

#### Scenario: Positional differentiation
- **WHEN** displaying email categories
- **THEN** primary category appears before the subject, badges appear after

### Requirement: Consistent ordering of categories

The system SHALL display categories in a consistent, predictable order to aid user comprehension. Order SHALL be: user-assigned categories first (in assignment order), then matched rule categories (in rule definition order).

#### Scenario: Mixed user and rule categories
- **WHEN** email has user-assigned "Personal" and rule-matched "Action Required"
- **THEN** "Personal" appears first, then "Action Required"

#### Scenario: Multiple rule matches
- **WHEN** email matches rules for "Work" and "Action Required"
- **THEN** categories appear in the order the rules were defined

### Requirement: Truncation of category list

When an email belongs to many categories, the system SHALL truncate the display with an indicator of how many more categories exist.

#### Scenario: Many categories
- **WHEN** email belongs to 5 categories but UI can only display 3
- **THEN** TUI shows 3 categories plus "+2 more"

#### Scenario: Hover/tooltip for full list
- **WHEN** user hovers over truncated categories
- **THEN** full list of all categories is shown in a tooltip
