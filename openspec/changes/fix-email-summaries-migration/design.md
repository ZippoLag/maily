## Context

See proposal.md — Why. Git history confirms the mechanism: commit 730ccf8 (tui-email-expansion-and-summary) inserted the `email_summaries` table and its index into the already-shipped v1 migration block while `SCHEMA_VERSION` stayed 1. The migration runner executes the v1 block only when `current < 1`, so databases migrated by the older foundation code never create the table; they then accept the v2 migration and sit at version 2 with no `email_summaries`. The existing migration test missed it because it builds a *minimal* v1 schema and never asserts `email_summaries` exists.

## Goals / Non-Goals

- **Goals**: Repair every existing database without data loss; make summary generation resilient to cache failures; lock both behaviors in with regression tests.
- **Non-Goals**: No summary-feature changes; no rescan of user data; no restructuring of the v1/v2 migrations already shipped.

## Decisions

- **Ship a v3 migration with idempotent DDL** (`CREATE TABLE IF NOT EXISTS email_summaries`, `CREATE INDEX IF NOT EXISTS summaries_message_idx`) and `SCHEMA_VERSION = 3`. Existing v1/v2 databases run the v3 block and get the table; fresh databases already have it from the v1 block, so the v3 block is a safe no-op. Alternative — editing the v1 block retroactively — rejected: it cannot repair already-migrated databases and repeats the anti-pattern that caused the bug.
- **Fold the summary cache read/write into the existing degraded-fallback path** in `_generate_summary`: the cache is an optimization, so a cache failure should behave exactly like an inference failure (deterministic preview), not crash the TUI. Alternative — a dedicated friendly error — rejected: the preview is the designed degraded behavior and needs no new UX.
- **Regression test builds the original foundation schema** (the exact v1 DDL from before 730ccf8, without `email_summaries`), seeds data, then asserts migration to version 3 creates the table + index and preserves the data — reproducing the user's failure mode precisely. The existing `test_existing_v1_database_migrates_without_data_loss` fixture and its `version == 2` assertion are updated to the new expectations.

## Risks / Trade-offs

- [Fresh databases run the v3 block] → no-op by construction (`IF NOT EXISTS`); verified by running the full suite against new databases.
- [Other tables retro-added to shipped migrations] → git history shows `email_summaries` is the only one; v3 covers it. The spec's modified "Versioned SQLite persistence" requirement makes future in-place edits contractually out of bounds.
- [Existing tests assert `schema_version == 2`] → updated to 3 as part of the change; the migration test now also asserts the previously-missing table.
