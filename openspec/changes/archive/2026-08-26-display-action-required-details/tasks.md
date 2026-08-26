## 1. Modify CLI render_human function

- [x] 1.1 Update `render_human` in `maily/cli.py` to detect "Action Required" category and iterate through its messages, displaying subject and sender_email for each
- [x] 1.2 Handle empty subject case by displaying "(no subject)" as specified in the spec
- [x] 1.3 Verify the output format matches: `  - <subject> (<sender_email>)` with two-space indent

## 2. Add tests for new behavior

- [x] 2.1 Add test case to `tests/test_cli.py` (or create it) for scan output with Action Required emails showing title and sender
- [x] 2.2 Add test case for empty subject handling in Action Required emails
- [x] 2.3 Add test case for scan output with no Action Required emails (only count shown)
- [x] 2.4 Verify existing tests still pass (no regression in other categories)

## 3. Verification

- [x] 3.1 Run `pytest tests/` to verify all tests pass including new ones
- [x] 3.2 Manually test with a scan that has Action Required emails to verify human-readable output shows details correctly
- [x] 3.3 Verify `--json-format` output remains unchanged
