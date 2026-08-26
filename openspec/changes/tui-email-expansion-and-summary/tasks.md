## 1. Email Expansion

- [ ] 1.1 Update Tree node creation in tui.py to support expandable email nodes, verify Enter key expands email
- [ ] 1.2 Add expanded content display (sender + body) to email nodes, verify content appears on expand
- [ ] 1.3 Add visual indicators (▼/▶) for expanded/collapsed state, verify indicators show correctly
- [ ] 1.4 Implement body text wrapping for terminal width, verify long lines wrap properly
- [ ] 1.5 Handle empty body display with "(no body)" indicator, verify empty emails show placeholder
- [ ] 1.6 Format sender display as "From: Name <email@example.com>", verify sender info is clear

## 2. Summary Hotkey

- [ ] 2.1 Add 'S' hotkey binding to BrowseApp, verify hotkey is active when email selected
- [ ] 2.2 Update footer to show "S: summarize" help text, verify hotkey appears in footer
- [ ] 2.3 Implement summary generation with inference fallback, verify both paths work
- [ ] 2.4 Create SummaryModal widget for displaying summary, verify modal opens on hotkey press
- [ ] 2.5 Add modal dismiss functionality (Escape key), verify modal can be closed
- [ ] 2.6 Handle hotkey on category node (no-op or error), verify no error on category selection

## 3. Summary Generation

- [ ] 3.1 Create summarize_email() function with inference/deterministic logic, verify function works
- [ ] 3.2 Add inference prompt for summary generation, verify prompt produces good summaries
- [ ] 3.3 Implement deterministic fallback (first 200 chars), verify fallback text is clear
- [ ] 3.4 Label deterministic summaries as "Preview", verify user knows it's truncated
- [ ] 3.5 Handle inference errors gracefully with fallback, verify no crashes on error

## 4. Database Cache

- [ ] 4.1 Add email_summaries table to db.py, verify table is created
- [ ] 4.2 Add Database methods: get_summary(), store_summary(), verify methods work
- [ ] 4.3 Integrate caching into summary generation, verify summaries are cached and reused

## 5. Integration and Testing

- [ ] 5.1 Add test: email expands to show sender and body, verify expansion works
- [ ] 5.2 Add test: summary hotkey generates and displays summary, verify end-to-end
- [ ] 5.3 Add test: inference disabled uses deterministic fallback, verify fallback works
- [ ] 5.4 Add test: inference unavailable uses deterministic fallback, verify fallback works
- [ ] 5.5 Add test: summary is cached and reused, verify no duplicate generation
- [ ] 5.6 Add test: TUI remains read-only (no Gmail mutations), verify no side effects

## 6. Documentation

- [ ] 6.1 Update README.md with email expansion usage, verify docs are clear
- [ ] 6.2 Add TUI summary hotkey documentation to README.md, verify keyboard shortcut documented
