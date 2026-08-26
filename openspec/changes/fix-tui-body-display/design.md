## Context

See proposal.md — Why. The categorized-messages query in `maily/db.py` feeds the TUI category tree and the digest; it selected subject, sender, and category fields but omitted the `body` column. Bodies have always been persisted by `upsert_messages`.

## Goals / Non-Goals

- **Goals**: Make the message body available to TUI rows and digest input; cover with a regression test.
- **Non-Goals**: No display-layout changes, no rescan or migration — stored data is reused as-is.

## Decisions

- **Include `m.body` in the existing SELECT** rather than a separate lookup: the query already joins messages, one column is the minimal change, and TUI rendering stays a single-pass read. Alternative (a per-node body lookup) was rejected as N+1 and more code.

## Risks / Trade-offs

- [Larger rows returned for large mailboxes] → mitigated: SQLite reads only requested columns and body text is already stored, so there is no new storage or network cost.
