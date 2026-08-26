## Why

Users with large email backlogs (5000+ unread, 12000+ read emails) need specialized workflows to tackle "email debt" efficiently. This change captures **corner cases and large-scale scenarios** that the standard triage flow doesn't handle well, including **progressive processing** and **AI-assisted suggestions** for batch actions.

This is specifically motivated by the user's stated problem: most of 17000+ emails could be safely deleted, but some need to be kept and others require action - manual triage is impractical at this scale.

## What Changes

- **New**: Long-running scan mode with progress tracking (overnight processing)
- **New**: Progressive fetch-analysis-suggest workflow (process in batches, suggest actions, user reviews)
- **New**: Performance optimizations for handling thousands of emails
- **New**: Memory-efficient processing (stream emails, don't load all in memory)
- **New**: Error resilience (continue on individual email failures, report at end)
- **New**: Configurable batch sizes for progressive processing
- **New**: AI suggestions for batch actions (delete, archive, categorize) with confidence scores
- **New**: Suggested action review interface (show suggestions, user accepts/rejects in bulk)
- **Modified**: Scan timeout handling for long operations
- **Modified**: Database to handle large volumes efficiently

**Non-Goals (for this change):**
- Actual Gmail mutations (delete, archive, mark read) - these remain read-only suggestions
- Real-time sync (this is batch/overnight oriented)

## Capabilities

### New Capabilities
- `sync/long-running-mode`: Extended scan mode for processing large backlogs overnight
- `sync/progressive-processing`: Fetch and analyze emails in configurable batches
- `sync/error-resilience`: Continue processing on individual failures, aggregate errors
- `classification/bulk-suggestions`: AI suggests batch actions (delete/archive/categorize) for groups of emails
- `tui/suggestion-review`: Interface for reviewing and accepting/rejecting suggested batch actions
- `performance/memory-efficiency`: Stream-based processing to avoid memory exhaustion
- `gmail/rate-limit-handling`: Respect Gmail API quotas, pause/resume as needed

### Modified Capabilities
- `email-triage`: Updated to handle streaming/batched processing
- `local-state`: Extended to track progressive sync state

## Impact

**Affected code:**
- `maily/sync.py` - Add long-running mode, progressive processing, error resilience
- `maily/gmail.py` - Add rate limit handling, batch fetching
- `maily/tui.py` - Add suggestion review interface
- `maily/db.py` - Optimize for bulk inserts, add progress tracking
- `maily/config.py` - Add batch size, timeout, long-running mode config
- New module: `maily/suggestions.py` - Batch action suggestion logic

**New data:**
- Config: `scan.batch_size`, `scan.long_running_mode`, `scan.timeout_hours`
- Database: `sync_batches` table, `suggestion_cache` table

**Dependencies:**
- For AI suggestions: Ollama (optional)
- Gmail API rate limit awareness

## User Context

This change is critical for users with:
- Large email backlogs (1000s of emails)
- Need to process email debt progressively
- Want AI assistance to identify deletable vs. keepable emails at scale
- Limited time for manual triage

The workflow enables:
1. Start overnight scan: `maily scan --long-running --start-date 2020-01-01`
2. Process runs in batches, shows progress
3. AI suggests: "These 500 emails from 'newsletter@example.com' can likely be deleted"
4. User reviews suggestions in TUI, accepts/rejects in bulk
5. Suggestions stored for later action (future mutation change)
