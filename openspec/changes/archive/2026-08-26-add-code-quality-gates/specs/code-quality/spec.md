## Purpose

Establishes the project's code-quality gates: every commit is automatically checked for formatting, linting, type correctness, and test coverage, and a reproducible development environment guarantees the checks run consistently.

## ADDED Requirements

### Requirement: Formatting enforcement

The project SHALL enforce a consistent code format on all Python source files using ruff's default style (line length 88).

#### Scenario: Unformatted code is committed
- **WHEN** a developer commits Python code that does not conform to the enforced format
- **THEN** the commit is blocked until the code is formatted

#### Scenario: Formatted code is committed
- **WHEN** a developer commits conforming Python code
- **THEN** the formatting check passes and the commit proceeds

### Requirement: Linting enforcement

The project SHALL lint all Python source files with ruff on every commit, and lint errors SHALL block the commit.

#### Scenario: Lint error present
- **WHEN** a commit contains a lint error (unused import, undefined name, or other rule violation)
- **THEN** the commit is blocked and the offending locations are reported

### Requirement: Type checking

The project SHALL type-check all Python source files with mypy on every commit, and type errors SHALL block the commit.

#### Scenario: Type error present
- **WHEN** a commit contains a mypy-detectable type error
- **THEN** the commit is blocked and the error is reported with file and line

#### Scenario: No type errors
- **WHEN** mypy completes without errors
- **THEN** the type check passes and the commit proceeds

### Requirement: Test coverage gate

The project SHALL run the test suite with branch coverage on every commit and SHALL enforce a minimum coverage threshold; commits below the threshold SHALL be blocked, and the report SHALL list uncovered lines.

#### Scenario: Coverage below threshold
- **WHEN** the commit's test run reports coverage below the configured minimum
- **THEN** the commit is blocked and the uncovered statements are listed

#### Scenario: Coverage at or above threshold
- **WHEN** the test run meets the coverage minimum
- **THEN** the coverage gate passes and the commit proceeds

### Requirement: Commit gating

The project SHALL run the formatting check, lint, type check, and coverage gate automatically before every commit, and any failing gate SHALL block the commit.

#### Scenario: Any gate fails
- **WHEN** a developer attempts to commit and any quality gate fails
- **THEN** the commit is aborted and the failing gate is reported

#### Scenario: All gates pass
- **WHEN** all quality gates pass on a commit
- **THEN** the commit completes normally

### Requirement: Reproducible development environment

The project SHALL provide a documented, reproducible development environment: all development dependencies SHALL be installed into a dedicated project virtual environment by a single documented command, and the quality gates SHALL run against that environment.

#### Scenario: Fresh development setup
- **WHEN** a developer clones the repository and runs the documented setup command
- **THEN** a project virtual environment with all development dependencies is created and the quality gates run successfully against it

#### Scenario: Gates use the project environment
- **WHEN** the quality gates execute
- **THEN** they use the project virtual environment rather than an ad-hoc or global environment
