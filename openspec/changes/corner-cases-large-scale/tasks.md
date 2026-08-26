## 1. Long-Running Mode Foundation

- [ ] 1.1 Add --long-running CLI flag to scan command, verify flag is recognized
- [ ] 1.2 Add long_running_mode config option, verify config is parsed
- [ ] 1.3 Add scan timeout override for long-running mode, verify no timeout on long scans
- [ ] 1.4 Add lock file to prevent concurrent scans, verify only one scan runs at a time
- [ ] 1.5 Add graceful interrupt handling (Ctrl+C), verify progress is saved on interrupt

## 2. Progress Tracking

- [ ] 2.1 Add sync_state table to db.py with last_date, total_processed, status fields
- [ ] 2.2 Add Database methods for sync state CRUD, verify methods work
- [ ] 2.3 Implement periodic checkpoint saving, verify checkpoints are saved every 100 emails
- [ ] 2.4 Add checkpoint configuration (interval_emails, interval_seconds), verify configurable
- [ ] 2.5 Add resume from checkpoint logic, verify scan resumes from last checkpoint
- [ ] 2.6 Add ProgressLogger class for structured logging, verify logs are written

## 3. Batch Processing

- [ ] 3.1 Implement chunked email fetching in gmail.py, verify emails fetched in batches
- [ ] 3.2 Add batch processing to scan() function, verify batches are processed sequentially
- [ ] 3.3 Implement memory cleanup between batches, verify memory stays bounded
- [ ] 3.4 Add batch size configuration, verify configurable batch sizes
- [ ] 3.5 Add batch database commit, verify efficient bulk inserts

## 4. Progress Reporting

- [ ] 4.1 Add CLI progress reporter, verify progress prints to stdout
- [ ] 4.2 Add TUI progress bar widget, verify progress bar displays
- [ ] 4.3 Implement ETA calculation, verify ETA updates correctly
- [ ] 4.4 Add multi-level verbosity (default, verbose, debug), verify all levels work
- [ ] 4.5 Add progress logging to file, verify logs are written in JSON Lines format

## 5. Error Resilience

- [ ] 5.1 Implement error classification (network, quota, parsing, etc.), verify errors categorized
- [ ] 5.2 Add continue-on-error logic, verify scan continues after individual failures
- [ ] 5.3 Implement aggregate error reporting, verify all errors reported at end
- [ ] 5.4 Add automatic retry with exponential backoff, verify retries work with backoff
- [ ] 5.5 Add max retries configuration, verify max retries is respected
- [ ] 5.6 Add partial success reporting, verify partial results are shown
- [ ] 5.7 Add error log file, verify errors written to scan_errors.log

## 6. Rate Limit Handling

- [ ] 6.1 Add rate limit error detection, verify 429 errors are caught
- [ ] 6.2 Add quota exceeded error detection, verify quota errors are caught
- [ ] 6.3 Implement exponential backoff with jitter, verify backoff times increase with jitter
- [ ] 6.4 Add quota usage tracking, verify requests are counted
- [ ] 6.5 Add estimated quota remaining, verify estimation is accurate
- [ ] 6.6 Implement pause and auto-resume on quota exhaustion, verify pause/resume works
- [ ] 6.7 Add quota configuration options, verify custom settings work
- [ ] 6.8 Add clear quota error messages, verify messages are user-friendly

## 7. Memory Efficiency

- [ ] 7.1 Implement stream-based email processing, verify emails processed in stream
- [ ] 7.2 Add batch database commits, verify bulk inserts work
- [ ] 7.3 Implement LRU cache for email bodies, verify cache evicts LRU items
- [ ] 7.4 Add configurable cache size, verify size is respected
- [ ] 7.5 Add memory usage monitoring, verify warnings at 80% usage
- [ ] 7.6 Add memory limit configuration, verify limit is respected
- [ ] 7.7 Use generators for iteration, verify memory-efficient iteration

## 8. Bulk Suggestions

- [ ] 8.1 Create suggestion grouping function, verify emails grouped by patterns
- [ ] 8.2 Implement deterministic bulk suggestion generation, verify suggestions work without inference
- [ ] 8.3 Add confidence scoring for bulk suggestions, verify scores are reasonable
- [ ] 8.4 Add inference-based bulk suggestions (optional), verify AI suggestions work
- [ ] 8.5 Create BulkSuggestion model, verify model stores suggestion data
- [ ] 8.6 Implement sample-based analysis for performance, verify sampling works on large sets

## 9. Suggestion Review TUI

- [ ] 9.1 Add suggestion review mode to TUI, verify mode activates on suggestions
- [ ] 9.2 Create SuggestionReviewWidget for displaying suggestion list, verify list displays correctly
- [ ] 9.3 Add confidence indicators (colors), verify High=green, Medium=yellow, Low=gray
- [ ] 9.4 Implement suggestion filtering, verify filtering by confidence/type works
- [ ] 9.5 Add suggestion preview (show affected emails), verify preview works with sampling
- [ ] 9.6 Implement bulk accept/reject, verify multiple suggestions can be accepted at once
- [ ] 9.7 Add suggestion execution (categorization immediate, mutations queued), verify execution works
- [ ] 9.8 Add suggestion history tracking, verify history is stored
- [ ] 9.9 Add undo for categorization suggestions, verify categories can be removed

## 10. Mutation Intent Storage

- [ ] 10.1 Add mutation_intents table to db.py, verify table is created
- [ ] 10.2 Add Database methods for intent CRUD, verify methods work
- [ ] 10.3 Store delete/archive/mark_read intents when suggestions accepted, verify intents stored
- [ ] 10.4 Add intent review in TUI, verify user can view pending intents
- [ ] 10.5 Add intent export/import (optional), verify intents can be shared

## 11. CLI Enhancements

- [ ] 11.1 Add --start-date and --end-date CLI arguments, verify date parsing works
- [ ] 11.2 Add --last N(days|weeks|months) CLI argument, verify relative dates work
- [ ] 11.3 Add --include-read CLI flag, verify read emails are included
- [ ] 11.4 Add --batch-size CLI argument, verify batch size is respected
- [ ] 11.5 Add scan status command, verify status can be queried
- [ ] 11.6 Add scan resume command, verify resume works after interruption
- [ ] 11.7 Add scan reset command, verify state can be reset

## 12. Config Updates

- [ ] 12.1 Add [scan] section with long_running options, verify config is parsed
- [ ] 12.2 Add [performance] section with memory limits, verify limits are respected
- [ ] 12.3 Add [suggestions] section with confidence thresholds, verify configurable
- [ ] 12.4 Update default config.toml with new options (commented), verify examples are clear

## 13. Integration and Testing

- [ ] 13.1 Add test: long-running scan with 1000 emails, verify completes without timeout
- [ ] 13.2 Add test: progress checkpoint and resume, verify resumption works
- [ ] 13.3 Add test: error resilience with failed emails, verify scan continues
- [ ] 13.4 Add test: rate limit handling, verify backoff and resume work
- [ ] 13.5 Add test: memory usage with 10K emails, verify memory stays bounded
- [ ] 13.6 Add test: quota exhaustion pause/resume, verify auto-resume works
- [ ] 13.7 Add test: bulk suggestion generation, verify suggestions are generated
- [ ] 13.8 Add test: suggestion review in TUI, verify review workflow works
- [ ] 13.9 Add test: partial success reporting, verify errors are reported
- [ ] 13.10 Add test: default behavior unchanged, verify normal scan still works

## 14. Documentation

- [ ] 14.1 Update README.md with long-running scan usage, verify examples are clear
- [ ] 14.2 Add progress tracking documentation, verify users understand progress
- [ ] 14.3 Add error handling documentation, verify users know how to troubleshoot
- [ ] 14.4 Add rate limit handling documentation, verify quota behavior is clear
- [ ] 14.5 Add bulk suggestions documentation, verify suggestion workflow is clear
- [ ] 14.6 Add configuration reference for all new options, verify all options documented
