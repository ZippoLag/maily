## Purpose

Guarantees that the reading/preview pane occupies a fixed height at the bottom of the screen whenever it is visible, and gives the user a way to toggle it so it can never take over the whole interface.

## ADDED Requirements

### Requirement: Fixed-height preview pane
The reading pane SHALL occupy a fixed height at the bottom of the screen whenever it is visible. It MUST NOT expand to fill the whole screen. The email list SHALL take the remaining space above it.

#### Scenario: Pane stays fixed height
- **WHEN** the reading pane is visible and the screen is resized
- **THEN** the reading pane keeps its fixed bottom height and the email list fills the remaining space

#### Scenario: Long content does not grow the pane
- **WHEN** a selected email body is long
- **THEN** the reading pane still occupies only its fixed height at the bottom (content scrolls within the pane)

### Requirement: Toggle visibility
The TUI SHALL provide a key binding that toggles the reading pane's visibility on and off, so the email list can use the full screen height when desired.

#### Scenario: Toggle pane off
- **WHEN** the reading pane is visible and the user presses the toggle key
- **THEN** the reading pane is hidden and the email list expands to the full screen height

#### Scenario: Toggle pane on
- **WHEN** the reading pane is hidden and the user presses the toggle key
- **THEN** the reading pane is shown again at its fixed bottom height