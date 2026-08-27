## 1. Fix categorized-messages query

- [x] 1.1 Add `m.body` to the SELECT in `Database.categorized_messages()` so TUI rows carry the message body
- [x] 1.2 Add regression test `test_categorized_messages_includes_body` asserting the body flows through to the returned rows

## 2. Verification

- [x] 2.1 Run the full test suite (`pytest`) and confirm all tests pass
- [x] 2.2 Verify a scanned message with a body renders its content in `maily tui` (repro script confirmed the row carries the real body, not "(no body)")
