## 1. Gmail Client Updates

- [x] 1.1 Add date range parsing in gmail.py for CLI args and config, verify all date formats work
- [x] 1.2 Add include_read parameter to today_unread() method, verify read emails are fetched when enabled
- [x] 1.3 Implement date-based queries for Gmail API, verify correct date filtering
- [x] 1.4 Add rate limit handling with exponential backoff, verify retries work on rate limit
- [x] 1.5 Add quota error handling, verify graceful failure on quota exceeded

## 2. Sync Logic Updates

- [x] 2.1 Add chunked processing to scan() function, verify emails processed in date chunks
- [x] 2.2 Implement progress reporting callback system, verify progress updates are sent
- [x] 2.3 Add configurable chunk sizes (day/week/month/year), verify all chunk sizes work
- [x] 2.4 Add stream-based memory-efficient processing, verify memory stays bounded
- [x] 2.5 Update fingerprint logic for historical emails, verify caching works correctly

## 3. Progress Reporting

- [x] 3.1 Add ProgressReporter class for CLI output, verify CLI shows progress
- [x] 3.2 Add progress bar widget for TUI, verify TUI shows progress bar
- [x] 3.3 Implement ETA calculation based on processing rate, verify ETA updates correctly
- [x] 3.4 Add verbose/debug progress modes, verify all levels work
- [x] 3.5 Exclude progress from JSON output, verify JSON remains clean

## 4. Database Updates

- [ ] 4.1 Add sync_state table to db.py, verify table is created
- [ ] 4.2 Add Database methods: get_sync_state(), save_sync_state(), reset_sync_state()
- [ ] 4.3 Add sync state tracking to scan() function, verify state is saved periodically
- [ ] 4.4 Update messages table to handle historical emails, verify no duplicates

## 5. CLI Updates

- [ ] 5.1 Add --start-date and --end-date CLI arguments, verify date parsing works
- [ ] 5.2 Add --last N(days|weeks|months) CLI argument, verify relative dates work
- [ ] 5.3 Add --include-read CLI flag, verify read emails are included
- [ ] 5.4 Add --chunk-size CLI argument, verify chunk size is respected
- [ ] 5.5 Add --verbose and --debug flags for progress output, verify output levels
- [ ] 5.6 Update scan command help text, verify all options documented

## 6. Config Updates

- [ ] 6.1 Add [scan] section to config with date_range, include_read, chunk_size
- [ ] 6.2 Add config validation for date ranges, verify invalid dates are rejected
- [ ] 6.3 Update default config.toml with commented examples, verify examples are clear
- [ ] 6.4 Add config migration handling for new options, verify old configs work

## 7. TUI Updates

- [ ] 7.1 Implement virtual scrolling in BrowseApp, verify performance with 10K emails
- [ ] 7.2 Add lazy loading for email bodies, verify bodies load on expand
- [ ] 7.3 Add result count display (e.g., "1-50 of 5000"), verify count updates correctly
- [ ] 7.4 Add keyboard navigation (Page Up/Down, Home/End), verify navigation works
- [ ] 7.5 Add date-based grouping in tree, verify emails grouped by date
- [ ] 7.6 Add progress bar display during scan, verify progress is visible

## 8. Digest Current View

- [ ] 8.1 Add 'd' hotkey for digest, verify hotkey works
- [ ] 8.2 Create digest generation function with inference fallback, verify both paths work
- [ ] 8.3 Create DigestModal widget, verify modal displays digest
- [ ] 8.4 Add modal dismiss functionality, verify user can close digest
- [ ] 8.5 Implement digest caching, verify same view uses cache
- [ ] 8.6 Add digest to footer help text, verify hotkey is documented

## 9. Integration and Testing

- [ ] 9.1 Add test: historical date range scan, verify emails from past are fetched
- [ ] 9.2 Add test: include_read scans read emails, verify read emails are included
- [ ] 9.3 Add test: chunked processing with progress, verify chunks and progress work
- [ ] 9.4 Add test: rate limit handling, verify backoff works
- [ ] 9.5 Add test: TUI with 10K emails, verify virtual scrolling performs
- [ ] 9.6 Add test: digest current view, verify digest generates correctly
- [ ] 9.7 Add test: resume interrupted scan, verify state is restored
- [ ] 9.8 Add test: default behavior unchanged, verify today-only still works

## 10. Documentation

- [ ] 10.1 Update README.md with historical scan examples, verify docs are clear
- [ ] 10.2 Add CLI argument documentation to README.md, verify all args documented
- [ ] 10.3 Add config option documentation to README.md, verify options documented
- [ ] 10.4 Add TUI navigation docs for large result sets, verify keyboard shortcuts documented
