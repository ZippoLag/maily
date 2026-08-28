## 1. Fixed-height pane

- [x] 1.1 Assign the reading pane a fixed `height`/`max_height` and the tree `height=1fr` in `compose`, and verify a test asserts the pane height stays fixed while the tree expands
- [x] 1.2 Ensure long body content scrolls within the pane instead of growing it, and verify a test covers the long-content case

## 2. Toggle visibility

- [x] 2.1 Add a toggle key binding and `action_toggle_read_pane` that hides/shows the reading pane, and verify a test asserts display flips and the list fills the screen when hidden

## 3. Full verification

- [ ] 3.1 Run the full gate: `ruff check`, `ruff format --check`, `mypy`, `pytest`, and `openspec validate --all` all pass