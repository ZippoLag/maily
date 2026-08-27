## 1. Row rendering

- [x] 1.1 Add a helper that formats an email row as `[ ]/#[x] sender... subject` and verify unit tests cover single vs multiple senders and marked vs unmarked
- [x] 1.2 Use the helper in the tree/row render so lines show the new format, and verify the render test passes

## 2. Expand removal

- [x] 2.1 Remove the expand/collapse triangles and the expand action, removing its bindings from the BINDINGS table, and verify py_compile plus the render tests pass
- [x] 2.2 Rebind Enter and Space to toggle the mark on the highlighted email (removing `m`) and verify a test asserts Enter marks the highlighted email

## 3. Key binding tidy-up

- [x] 3.1 Add `Ctrl+M` action that toggles mark/unmark for all emails in the current date scope and verify a test covers the current-date scope (not just visible rows)
- [x] 3.2 Remove `Ctrl+A`, `Ctrl+D`, and Shift+arrow bindings and the now-dead handlers and verify the BINDINGS table matches the spec

## 4. Selection/marking semantics + shared actions

- [x] 4.1 Extract a shared `resolve_target_emails` (marked → selected → none) helper and verify unit tests cover each fallback branch
- [x] 4.2 Re-point the `c` edit-categories action at the shared helper and verify a test asserts marked, then selected, then no-op behavior

## 5. Sorting disclosure

- [x] 5.1 Make the `s` action `notify()` the current sorting logic before applying it and verify a test asserts the message is shown

## 6. Docs

- [x] 6.1 Update the README keyboard-shortcuts table and interaction docs for the new keys and check the table lists no removed bindings

## 7. Full verification

- [x] 7.1 Run the full gate: `ruff check`, `ruff format --check`, `mypy`, `pytest`, and `openspec validate --all` all pass