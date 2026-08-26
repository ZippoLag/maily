## Why

`maily tui` crashed on startup with `ImportError: cannot import name 'ModalScreen' from 'textual.widgets'` even with the `tui` extra installed, because `ModalScreen` is exported from `textual.screen`, not `textual.widgets`. The import sat inside a lazy block that the unit suite never executed, so the broken import shipped undetected.

## What Changes

- `maily/tui.py` imports `ModalScreen` from `textual.screen` (its correct module)
- The lazy Textual import is extracted into a module-level `_load_textual()` so import resolution is directly unit-testable
- `maily/cli.py` turns a missing Textual into `maily: Install maily with the 'tui' extra to use the TUI` on stderr with exit code 1, instead of a raw traceback
- `textual` added to the `dev` extra so import resolution is exercised in test environments
- Version bumped 0.1.0 → 0.2.0 per AGENTS.md
- No breaking changes

## Capabilities

### New Capabilities
- `tui/startup`: TUI startup behavior — launches when the `tui` extra is installed and reports a clear, actionable error when Textual is missing

### Modified Capabilities
(none)

## Impact

- `maily/tui.py`: corrected import + `_load_textual()` extraction
- `maily/cli.py`: friendly error path for missing Textual
- `pyproject.toml`: `textual` in the `dev` extra, version 0.2.0
- `tests/test_tui.py`: import-resolution and missing-Textual tests; `tests/test_smoke.py`: version assertion
