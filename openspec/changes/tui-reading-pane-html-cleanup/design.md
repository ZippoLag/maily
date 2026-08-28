# Design: TUI Reading Pane HTML Cleanup

## Context

See proposal.md — Why. `email_pane_text` in `tui.py` currently wraps the raw `body` string. HTML bodies contain markup that looks broken when wrapped and displayed.

## Goals / Non-Goals

- **Goals**: Convert HTML bodies to clean Markdown via `html2text` before wrapping/display; pass plain-text through; fall back gracefully on failure. Add `html2text` to dependencies.
- **Non-Goals**: No rich terminal rendering of HTML (no colors/links styling). No changes to how the body is stored.

## Decisions

- **Use `html2text`** (per user decision): it converts HTML to Markdown with reasonable default output. Add as a runtime dependency in `pyproject.toml`.
- **Detect HTML before conversion**: only convert when the body looks like HTML (contains `<`-tag patterns); otherwise keep it as-is. Wrapping logic in `email_pane_text` stays and wraps the converted text.
- **Wrap conversion in a helper** `html_to_readable(body)`: returns converted text on success; on `ModuleNotFoundError`/exception or if the input has no HTML, returns the original body. This keeps `email_pane_text` resilient and testable.
- **Graceful fallback**: if `html2text` is unavailable at runtime, the helper returns the sanitized/raw body and the TUI keeps working.

## Risks / Trade-offs

- `html2text` adds a third-party dependency → pinned in `pyproject.toml`; fallback keeps the TUI functional if it's missing.
- Output styling is plain; we accept "clean text + minimal styling" scope as requested.

## Migration Plan

Add `html2text` to `pyproject.toml` and the lockfile (`pnpm`-style is not applicable; this is a Python project, so `pip install -e .` will install it).

## Open Questions

None.