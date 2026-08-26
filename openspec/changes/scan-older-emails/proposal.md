## Why

The current v1 implementation only scans **today's unread emails**, leaving users with large backlogs (e.g., 5000+ unread, 12000+ read emails) unable to triage historical messages. This change extends the scan capability to handle **any date range** with **progress feedback** and **UI scalability** for large mailboxes.

This addresses the original spec requirement to handle emails beyond just today, while ensuring the system remains responsive and provides visibility into long-running operations.

## What Changes

- **New**: Date range configuration for scans (specific dates, relative periods like "last 7 days", "this month")
- **New**: Date-based pagination (fetch by day/week/month/year chunks)
- **New**: Progress display during scan (show count of emails fetched, current date range being processed)
- **New**: Scan read emails in addition to unread
- **New**: Incremental sync tracking (remember last sync date per mailbox)
- **New**: TUI support for navigating large result sets (virtual scrolling, lazy loading)
- **New**: Summarize currently-displayed emails (AI-assisted digest of visible view)
- **Modified**: Gmail client to support historical queries and pagination
- **Modified**: Sync logic to handle larger result sets without hanging
- **Modified**: Database schema to track sync state for historical scans

## Capabilities

### New Capabilities
- `gmail/historical-sync`: Fetch emails from any date range, not just today
- `gmail/date-based-pagination`: Process emails in date chunks (day/week/month/year)
- `sync/progress-reporting`: Real-time progress feedback during large scans
- `tui/large-result-navigation`: UI patterns for handling thousands of emails
- `email-presentation/digest-current-view`: Summarize all currently displayed emails
- `local-state/sync-tracking`: Track incremental sync progress across sessions

### Modified Capabilities
- `gmail-account-access`: Extended to support historical date ranges
- `email-triage`: Updated to handle larger batch sizes

## Impact

**Affected code:**
- `maily/gmail.py` - Add date range queries, pagination, read email fetching
- `maily/sync.py` - Add progress reporting, chunked processing, incremental sync
- `maily/cli.py` - Add date range CLI arguments
- `maily/tui.py` - Add virtual scrolling, lazy loading, digest hotkey
- `maily/db.py` - Add sync state tracking tables
- `maily/config.py` - Add date range configuration

**New data:**
- Config: `scan.date_range`, `scan.include_read`, `scan.chunk_size`
- Database: `sync_state` table for tracking historical sync progress

**Dependencies:**
- None new (uses existing Gmail API, Python stdlib)

## User Context

This change is particularly important for users with:
- Large email backlogs (5000+ unread, 12000+ read emails)
- Need to triage historical emails without being blocked by UI/performance issues
- Want to process email debt progressively (overnight, in chunks)
