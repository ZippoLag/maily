## Context

This is a new Python application with no existing runtime architecture. The initial workflow must handle one Gmail account, process only today's unread inbox and spam messages, keep secrets out of ordinary files, and serve both CLI and TUI clients. See `proposal.md` and the capability specs for the motivation and observable behavior.

## Goals / Non-Goals

**Goals:**

- Establish a small service-oriented core shared by CLI and TUI clients.
- Make the first scan deterministic, resumable, and explicit about partial data.
- Keep Gmail access, persistence, classification, and presentation independently testable.
- Make future mutation permissions and historical synchronization additive rather than entangled with the first scan.

**Non-Goals:**

- Automatic scheduling or a resident background daemon.
- Gmail mutation commands or filter creation in this change.
- Multi-account identity management.
- Full-message historical mirroring on first launch.
- Remote inference or a hosted application service.

## Decisions

### Python package with shared application services

Use a conventional Python package with a console entry point and separate CLI/TUI adapters over shared use cases. This avoids duplicating synchronization and classification behavior between interfaces. A .NET implementation was considered, but Python better matches the requested local scripting and Gmail/Ollama ecosystem.

### Gmail REST adapter with narrow authorization

Encapsulate Gmail REST operations behind an adapter that returns application-level message and thread records. Use a user-provided Google OAuth desktop-client JSON file and the installed-app browser flow, with read-only scope for the foundation. Keep future mutation scopes and operations behind a separate authorization boundary. This is simpler to distribute than operating a backend and safer than depending on an external Gmail CLI.

### SQLite with explicit migrations

Use SQLite for indexed message, thread, category, classification, synchronization, and action-history data. Maintain schema revisions through Alembic migrations. SQLite provides indexed filtering and stable upserts for message IDs and threads while remaining a portable file under `~/.maily/`; flat JSON or CSV would make reruns, joins, and migration safety needlessly fragile.

### OS keyring for OAuth tokens

Use the platform keyring through a Python keyring integration, keyed to the one maily account. Persist only account identity and non-secret metadata in SQLite. Startup checks must fail clearly when no secure credential backend is available instead of silently falling back to plaintext.

### Configurable provider pipeline

Represent classification as a pipeline: normalized message metadata and body text first pass through configured deterministic rules, then unmatched messages go to an inference-provider interface. The default provider is Ollama over local HTTP with `gemma4:e2b`; timeout, endpoint, and model are configuration values. Provider failures become structured degraded status and unresolved messages become `Other`.

### Today-first synchronization and explicit completeness

Compute the local-day boundary once per run and use Gmail search criteria for unread messages in inbox and spam. Upsert messages and thread summaries transactionally, recording the query window and completion status. Do not infer read or older-unread totals from an intentionally narrow query; expose those values as deferred until a later historical-sync capability exists.

### Thin presentation adapters

The CLI renders a human-readable report or serializes a stable result object as JSON when `--json-format` is supplied. The initial TUI reads the same result and repository queries, supporting category navigation, expansion, inspection, and sorting only. It has no mutation commands, keeping irreversible behavior outside the first interactive surface.

## Risks / Trade-offs

- [Gmail OAuth setup is unfamiliar] → Provide an `init` or setup command with platform-neutral instructions, file validation, and a clear browser-based authentication flow.
- [OAuth scope changes may require re-consent] → Keep read-only scan authorization separate from future mutation authorization and surface reauthentication explicitly.
- [A large number of today's messages can make Ollama slow] → Apply deterministic rules first, bound provider timeouts, cache results by message content/configuration fingerprint, and report incomplete inference.
- [Email bodies contain sensitive personal data] → Send content only to the local configured provider, avoid body text in logs, and expose the provider endpoint in diagnostics.
- [The database may be interrupted during synchronization] → Use migrations plus transactional upserts and retain the previous completed sync marker until the new transaction commits.
- [Thread-level sorting requires complete thread metadata] → Store Gmail thread IDs and the observed first/last message timestamps; label sorting fields unavailable from the initial window as incomplete rather than inventing values.

## Migration Plan

1. On first launch, create `~/.maily/`, default configuration, the SQLite database, and apply migrations.
2. Guide the user through OAuth client setup and store tokens in the OS keyring.
3. Run a read-only today's-unread synchronization and persist its completion metadata.
4. Run deterministic classification and optional Ollama classification, then expose results through CLI, JSON, and TUI.
5. Future releases add migrations before enabling historical synchronization or Gmail mutations.

Rollback consists of stopping before any Gmail mutation, preserving the local database, and allowing the user to remove the maily keyring entry and state directory through a documented reset command. Since this foundation requests read-only access and performs no Gmail writes, rollback cannot alter Gmail data.

## Open Questions

None that change the agreed v1 scope or architecture. Exact CLI command names and visual TUI layout can be finalized during implementation.