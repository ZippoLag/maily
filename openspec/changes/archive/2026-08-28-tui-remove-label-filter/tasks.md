## 1. Remove binding and handler

- [x] 1.1 Remove the `l` → `filter_by_label` binding from `BINDINGS` and delete the dead handler, and verify a test asserts `l` performs no action
- [x] 1.2 Search for and remove any other dead label-filter references (filters/toolbar), and verify `grep filter_by_label` returns nothing

## 2. Docs

- [x] 2.1 Remove `l` from the README shortcuts table and any help text, and verify the table lists no `l` label-filter entry

## 3. Full verification

- [x] 3.1 Run the full gate: `ruff check`, `ruff format --check`, `mypy`, `pytest`, and `openspec validate --all` all pass