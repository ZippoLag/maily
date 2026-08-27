# Design: TUI List Interaction Rework

## Context

See proposal.md — Why. The current `tui.py` conflates selection (highlighted email) with marking (the checkbox set), uses Enter/Space to expand emails, binds `m`, Shift+arrows, `Ctrl+A`/`Ctrl+D`, and renders rows as `▲/▼ subject sender`. The reading pane already renders the selected email's body, so expansion is redundant.

## Goals / Non-Goals

- **Goals**: Remove expansion; make Enter/Space mark; unify `c` on marked→selected→none like `S`; make `s` disclose its logic; tidy bindings; standardize row rendering.
- **Non-Goals**: No new features beyond the requested key/label/scope changes. No changes to how marking is stored (the checkbox set stays as-is).

## Decisions

- **Row format `[ ]/#[x] sender... subject`**: We render the mark state first, then the truncated sender address, then subject. This matches the requested spec and is easy to test row-render helpers.
- **Enter and Space both mark** (toggle the highlighted email's checkbox), consistent with Textual's `action_mark`. We remove `m` to avoid duplicate-path confusion.
- **`Ctrl+M` marks/unmarks all emails in the current date scope** — the same date-scope helper the digest uses. This is a single `action_mark_all` bound to `ctrl+m`. `Ctrl+A` and `Ctrl+D` bindings are removed.
- **`c` reuses the existing `S` fallback resolution**: marked set → selected email → none. We extract the "target emails" resolution into a shared helper so `c` and `S` cannot drift.
- **`s` prints a `notify()` message describing the current sort** before/with applying it.
- **Shift+arrow bindings deleted** from the BINDINGS table.

## Risks / Trade-offs

- Removing `Ctrl+A` select-all could affect muscle memory → mitigated: `Ctrl+M` is the documented replacement for bulk marking.
- Changing Enter/Space semantics is a behavior break → mitigated: spec and README updated; existing tests updated to assert marking.

## Migration Plan

None required — local TUI-only behavior; no persistence or schema change.

## Open Questions

None.