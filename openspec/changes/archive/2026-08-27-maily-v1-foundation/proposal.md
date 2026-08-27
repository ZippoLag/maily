## Why

Email triage currently requires manually scanning a large Gmail inbox, while useful distinctions such as urgency, human correspondence, work, and newsletters are not represented by Gmail labels. This change establishes a local, privacy-preserving foundation for a one-account maily v1 that makes today's unread mail actionable without requiring a cloud service or automatic destructive behavior.

## What Changes

- Add a Python application with both a human-readable CLI and a read-only interactive TUI.
- Authenticate one Gmail account through guided Google OAuth desktop-client setup and store tokens through the operating system credential store.
- Synchronize only unread inbox and spam messages received today during the initial scan, using the configured local timezone.
- Persist synchronized message metadata, threads, classifications, sync state, and schema migrations in SQLite under `~/.maily/`.
- Run configurable deterministic classification rules before optional local Ollama inference using the configured model, defaulting to `gemma4:e2b`.
- Assign messages to one or more required categories and place unresolved messages in `Other`.
- Provide human-readable and `--json-format` scan output, plus TUI browsing with expand/collapse and sorting.
- Report incomplete historical read/unread counts as deferred rather than presenting partial data as complete.
- Keep Gmail mutations, historical synchronization, scheduling, multi-account support, cloud inference, and TUI mutation workflows out of this foundation change.

## Capabilities

### New Capabilities

- `gmail-account-access`: Guided single-account OAuth authentication and read-only Gmail synchronization.
- `local-state`: Secure local configuration, credential references, SQLite persistence, and migrations.
- `email-triage`: Today-focused unread message retrieval and deterministic-plus-local-LLM categorization.
- `email-presentation`: Human-readable CLI, JSON output, and read-only TUI browsing of triage results.

### Modified Capabilities

- None.

## Impact

- Adds a Python package and executable entry point, Gmail API and OAuth client dependencies, SQLite migration tooling, OS keyring integration, and optional Ollama HTTP integration.
- Adds files beneath `~/.maily/` at runtime; these remain local and are not committed to the repository.
- Requires users to create or download a Google OAuth desktop-client JSON file. maily will provide setup instructions and validate the file before authentication.
- The initial Gmail authorization is read-only. Broader permissions for future confirmed mutations will be introduced separately.