## Why

The reading pane currently shows raw HTML content, which is ugly and hard to read. We want to render a clean plain-text (and minimally styled) version of the email body instead.

## What Changes

- Convert HTML email bodies to **Markdown** using the `html2text` library, and render the result in the reading pane.
- Fall back gracefully when a body is already plain text or conversion fails, so raw HTML is never shown.
- **NEW DEPENDENCY:** `html2text` (Python, per the project's pip/Python stack).

## Capabilities

### New Capabilities
- `tui/reading-pane-content-cleanup`: HTML email bodies are converted to clean Markdown/plain text for display in the reading pane.

## Impact

- `pyproject.toml` — add `html2text` dependency.
- `maily/tui.py` — body rendering in the reading pane.
- New spec `tui/reading-pane-content-cleanup`.