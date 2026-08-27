## Why

Summarizing an email crashes the whole TUI with `OperationalError: no such table: email_summaries` on any database that was migrated before the summary feature shipped. Root cause: when the summary feature was added, the `email_summaries` table was inserted **inside the already-shipped v1 migration block** while `SCHEMA_VERSION` stayed 1. The v1 block only runs when `current < 1`, so pre-existing v1 databases never create the table — the migration runner never touches it again. The summary cache read (`get_summary`) also sits outside `_generate_summary`'s degraded-fallback guard, so the DB error terminates the TUI instead of falling back to the deterministic preview.

## What Changes

- **v3 migration**: bump `SCHEMA_VERSION` to 3 and add a migration that idempotently creates `email_summaries` + its index (`CREATE TABLE/INDEX IF NOT EXISTS`), repairing every existing database; a no-op for fresh ones
- **Degraded-fallback guard**: `_generate_summary` treats summary cache read/write failures like any other summary-path failure — degrade to the deterministic preview instead of raising
- **Regression test**: a v1 database built from the *original* foundation schema (no `email_summaries`) migrates to the current version with the table and index present and existing data intact
- No data loss, no rescan required — existing databases start summarizing (and caching) after migration

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `local-state`: Versioned-migration completeness — every supported existing database is brought fully to the current schema, including tables for capabilities added after the database's first migration
- `tui/email-summary`: Summary generation degrades gracefully when the summary cache is unavailable rather than terminating the TUI

## Impact

- `maily/db.py`: `SCHEMA_VERSION = 3` + v3 migration block
- `maily/tui.py`: `_generate_summary` cache read/write inside the degraded-fallback path
- `tests/test_local_state.py` or `tests/test_integration.py`: v1-with-original-schema migration regression test; summary-degradation test
