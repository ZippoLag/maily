## 1. Python Project Foundation

- [ ] 1.1 Create the Python package, executable entry point, development dependency configuration, and test layout; verify the package installs in a clean virtual environment with `pnpm`-managed project tooling unchanged.
- [ ] 1.2 Add configuration loading, default generation, restrictive `~/.maily/` directory creation, local timezone handling, and startup diagnostics; verify first launch creates defaults without overwriting an existing configuration.

## 2. Local Persistence and Secrets

- [ ] 2.1 Define the SQLite schema for account metadata, messages, threads, categories, classifications, synchronization runs, and action history; verify a fresh database initializes successfully.
- [ ] 2.2 Add versioned migrations and transactional repository operations for message/thread upserts and classification caching; verify migration upgrade tests pass and an interrupted transaction leaves the last completed sync intact.
- [ ] 2.3 Integrate OS credential-store token persistence and account identity references; verify tokens never appear in configuration, SQLite records, or logs and unsupported credential backends fail clearly.

## 3. Gmail Read-Only Access

- [ ] 3.1 Implement guided OAuth desktop-client file validation and one-account authentication with read-only scope; verify invalid files fail before network access and valid credentials record the account identity without plaintext tokens.
- [ ] 3.2 Implement the Gmail adapter for today's unread inbox and spam retrieval using the configured timezone boundary; verify mocked API tests separate spam from non-spam and exclude older or read messages.
- [ ] 3.3 Add sync error handling, retry boundaries, completion markers, and expired/revoked credential recovery; verify failed synchronization preserves the last successful local state and reports an actionable error.

## 4. Classification Pipeline

- [ ] 4.1 Add the required default categories and configurable deterministic rule evaluation; verify every required category exists and matching messages bypass inference.
- [ ] 4.2 Add the local Ollama provider with configurable endpoint, model, and timeout plus structured degraded-status reporting; verify valid responses are stored and unavailable providers fall back to `Other` without failing deterministic results.
- [ ] 4.3 Add classification fingerprints, cached reruns, multi-category assignments, and category counts; verify unchanged messages reuse cached results and overlapping categories count the message once per category.

## 5. CLI, JSON, and Read-Only TUI

- [ ] 5.1 Implement the daily scan CLI with human-readable status, category counts, deferred historical counts, and actionable Gmail/Ollama errors; verify the output labels incomplete historical data as deferred.
- [ ] 5.2 Implement `--json-format` serialization for synchronization status, messages, categories, counts, cached/degraded state, and errors; verify supported scan commands emit parseable JSON without decorative output.
- [ ] 5.3 Implement the initial read-only TUI with category navigation, expand/collapse, message inspection, and all specified sort criteria; verify browsing and sorting do not invoke Gmail mutation operations.
- [ ] 5.4 Add end-to-end tests using Gmail and Ollama fakes for first launch, empty results, partial failures, cached classification, CLI output, and TUI read-only browsing; verify the complete test suite passes.

## 6. User Setup Documentation

- [ ] 6.1 Document Python installation, Google OAuth desktop-client creation, first authentication, Ollama configuration, `~/.maily/` contents, reset behavior, and current v1 limitations; verify a fresh user can follow the instructions without undocumented credentials or services.