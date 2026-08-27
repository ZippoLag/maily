## Purpose

Defines how the TUI starts: it launches when the `tui` extra is installed, and reports a clear, actionable error when Textual is unavailable.

## ADDED Requirements

### Requirement: TUI launches when the tui extra is installed

The `maily tui` command SHALL launch the TUI when the `tui` extra is installed, resolving all Textual imports from their correct modules.

#### Scenario: tui extra installed
- **WHEN** the user runs `maily tui` with the `tui` extra installed
- **THEN** the TUI launches without an import error

### Requirement: Clear error when Textual is missing

When Textual is not installed, `maily tui` SHALL print a clear message instructing the user to install the `tui` extra and SHALL exit with a non-zero status.

#### Scenario: Textual unavailable
- **WHEN** the user runs `maily tui` without the `tui` extra installed
- **THEN** the CLI prints `maily: Install maily with the 'tui' extra to use the TUI` to stderr and exits with status 1, without a traceback
