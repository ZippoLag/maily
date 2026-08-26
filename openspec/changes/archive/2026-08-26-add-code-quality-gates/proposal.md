## Why

Every commit in this repo — including the per-task commits of the OpenSpec TDD workflow — currently passes with no quality gate at all. There is no formatter, linter, type checker, coverage tool, CI, or pre-commit hook; `pytest` is the only guard, and only when someone runs it. Style has already drifted (145 lines ≥ 88 chars, max 239). Measured coverage is 64% overall, with the TUI and CLI at 19% and 37%. This change adds a standard Python quality toolchain (ruff, mypy, pytest-cov) wired into a pre-commit hook so every commit is verified, plus a reproducible project venv to run it in.

## What Changes

- **ruff** for both linting and formatting, with the default style (line-length 88); applied repo-wide in a one-time reformat commit before gates are enforced
- **mypy** type checking at a non-strict baseline (the code is already ~83% annotated)
- **pytest-cov** with branch coverage; minimum threshold enforced (65% floor — just above today's 64% — ratcheting upward as coverage improves)
- **Pre-commit hook** running all four gates (ruff check, ruff format --check, mypy, pytest --cov) on every commit; any failure blocks the commit
- **Standardized project venv** (uv-managed, matching the existing `uv.lock`); all gates and dev dependencies run through it, and the devcontainer is wired to provide it
- No user-facing behavior changes to maily

## Capabilities

### New Capabilities
- `code-quality`: Commit-time quality gates (format, lint, type-check, coverage) and the reproducible development environment they run in

### Modified Capabilities
(none)

## Impact

- `pyproject.toml`: dev-extra dependencies (ruff, mypy, pytest-cov); `[tool.ruff]`, `[tool.mypy]`, `[tool.coverage.run]` sections
- `.githooks/pre-commit` (new) + `git config core.hooksPath` wiring; documented in README
- `uv.lock` regenerated; `.venv` becomes the canonical environment; `.devcontainer/devcontainer.json` setup to provide uv
- One-time reformat of `maily/` and `tests/`
- README: developer setup (venv creation, hook install) and gate descriptions
