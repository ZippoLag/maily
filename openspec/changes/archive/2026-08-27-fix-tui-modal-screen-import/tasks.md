## 1. Fix Textual import

- [x] 1.1 Extract the lazy Textual import into a module-level `_load_textual()` in `maily/tui.py` and import `ModalScreen` from `textual.screen`
- [x] 1.2 Add unit tests: `_load_textual()` resolves with `ModalScreen` coming from `textual.screen`; a missing Textual raises the friendly `RuntimeError`

## 2. CLI error handling

- [x] 2.1 `maily/cli.py` catches the missing-Textual case and prints `maily: Install maily with the 'tui' extra to use the TUI` to stderr, exiting 1 without a traceback

## 3. Test environment and version

- [x] 3.1 Add `textual` to the `dev` extra in `pyproject.toml`
- [x] 3.2 Bump version 0.1.0 → 0.2.0 in `pyproject.toml` and update the assertion in `tests/test_smoke.py`

## 4. Verification

- [x] 4.1 Run the full test suite (`pytest`) — all tests pass
- [x] 4.2 Confirm `maily --version` reports 0.2.0
