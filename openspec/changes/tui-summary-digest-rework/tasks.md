## 1. Digest scope and hotkey

- [ ] 1.1 Change the digest action to gather all current-date emails across all categories (ignoring mark/selection) and verify a unit test covers a multi-category current-date set with unmarked emails
- [ ] 1.2 Rebind digest from `d` to `D` and verify the BINDINGS table uses `D`
- [ ] 1.3 Generate one paragraph per non-empty category, skipping empty categories, and verify a test covers the skip-empty behavior
- [ ] 1.4 Format per-category totals as a multi-line list and verify a formatter test

## 2. Summarize scope

- [ ] 2.1 Rework the summarize action to use shared `resolve_target_emails` (marked → selected → none) and verify each fallback branch is tested
- [ ] 2.2 Produce one brief paragraph per marked email and verify a test asserts multiple paragraphs for multiple marked emails
- [ ] 2.3 When no marked and no selected email, do not open the summary view and show an explanatory message, and verify a test asserts the message and that the modal does not open

## 3. Full verification

- [ ] 3.1 Run the full gate: `ruff check`, `ruff format --check`, `mypy`, `pytest`, and `openspec validate --all` all pass