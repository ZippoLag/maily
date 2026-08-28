# Design: Remove label filter

## Context

See proposal.md — Why. `tui.py` binds `l` → `filter_by_label`, but the handler is non-functional. Dead bindings mislead users, so remove it.

## Goals / Non-Goals

- **Goals**: Remove the `l` binding, the `filter_by_label` action and any now-useless handler, and drop `l` from the README shortcuts table.
- **Non-Goals**: No re-implementation of label filtering. This is purely a removal.

## Decisions

- Delete the `("l", "filter_by_label", ...)` entry from the `BINDINGS` table and its handler. Check for any other label-filter UI (filters, toolbar) and remove dead references.
- Update README shortcuts table and any footer/help text mentioning `l`.

## Risks / Trade-offs

- Trivial removal; low risk. No migration.

## Migration Plan

None.

## Open Questions

None (the `l` removal is also touched by change 1's keyboard tidy-up; changes must land so this removal is not reintroduced — apply change 1 first, or ensure the earlier keyboard delta no longer claims `l` removal).