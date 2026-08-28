# Design: TUI Summary & Digest Rework

## Context

See proposal.md — Why. `tui.py` currently binds `s`=sort, `S`=summarize, `d`=digest. The digest summarizes only visible/selected emails and the summarize view's scope (marked vs selected) needs to align with the marking model introduced by change 1.

## Goals / Non-Goals

- **Goals**: Digest summarizes all current-date emails across all categories (one paragraph per non-empty category) with a formatted totals list and `D` hotkey. Summarize summarizes marked emails (individually), falling back to selected, or not opening with a message. Format category totals as lists.
- **Non-Goals**: No changes to inference/caching behavior. No changes to where summaries are cached or stored.

## Decisions

- **Digest scope = current date, all categories**: reuse the same date-scope logic that `Ctrl+M` (change 1) and the mark-all use, so "current date" is defined once. The digest reads messages for `date(today)` from `db.categorized_messages` grouped by category, skipping empty categories.
- **`D` (shift+d) replaces `d`** for digest; bind `S` and `D` explicitly (Textual treats uppercase as shift). `s` stays as sort.
- **Summarize scope resolution**: `marked` (all) → `selected` (single) → notify message + no open. Reuse the shared `resolve_target_emails` helper from change 1 so `S` and `c` stay consistent.
- **Per-email paragraphs**: for marked summaries, emit one paragraph per email; helper emits a heading/first-line per email.
- **Totals list formatting**: a small formatter that prints category counts as multi-line list text shown in the modal.

## Risks / Trade-offs

- None significant — modal-only view changes; existing tests updated.

## Migration Plan

None required.

## Open Questions

None.