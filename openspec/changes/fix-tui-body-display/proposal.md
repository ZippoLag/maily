## Why

The TUI displayed "(no body)" for every email after a scan because the categorized-messages query feeding the TUI tree never selected the message body column — the display layer received no body content even though bodies are stored locally. The digest/summary feature, which reads `body` from the same rows, was equally starved. Reported by a user who suspected stale scan data; investigation proved the bodies were always stored and only the display query dropped them.

## What Changes

- `Database.categorized_messages()` now includes `m.body` in its SELECT so every row the TUI renders carries the message body
- The "(no body)" placeholder now appears only for messages that genuinely have no body content
- Regression test `test_categorized_messages_includes_body` added
- No breaking changes; no rescan required — existing stored data renders correctly

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `local-state`: Categorized-message query results now include message body content

## Impact

- `maily/db.py`: one-column addition to the `categorized_messages()` SELECT
- `tests/test_local_state.py`: regression test for body presence in TUI rows
- Beneficiaries: `maily/tui.py` email node rendering and the digest/summary feature in `maily/cli.py`
