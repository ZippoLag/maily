## Context

See proposal.md — Why. `run_tui()` performed `from textual.widgets import ModalScreen` inside a lazy block; the symbol actually lives in `textual.screen`. The lazy block existed to produce a friendly "install the tui extra" error when Textual is absent, but it also meant the broken import was never executed by the unit suite (TUI tests covered only pure helpers).

## Goals / Non-Goals

- **Goals**: Correct import source; make the import path testable; keep the friendly missing-Textual error.
- **Non-Goals**: No TUI feature changes; no runtime dependency changes (the `tui` extra for end users is unchanged).

## Decisions

- **Import `ModalScreen` from `textual.screen`**: that is where it is exported; verified against installed Textual 8.x. Alternative (duplicating/vendoring the symbol) rejected — unnecessary and fragile.
- **Extract `_load_textual()` at module level**: makes the exact regression (import resolution) unit-testable without launching an app; `run_tui()` keeps its catch/raise contract.
- **Add `textual` to the `dev` extra**: guarantees test/CI environments execute the import path — the gap that let this bug ship.

## Risks / Trade-offs

- [Textual API drift in future versions] → mitigated by the import-resolution unit test failing loudly on such changes.
- [dev-extra dependency weight] → negligible; textual is already a package extra.
