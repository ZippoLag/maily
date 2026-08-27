## Context

Current maily only scans today's unread emails. Users with large backlogs (5000+ unread, 12000+ read) need to triage historical messages. The system must remain responsive during large scans and provide progress visibility.

Constraints:
- Gmail API has rate limits (varies by quota)
- Must not hang silently during long operations
- TUI must handle thousands of emails without crashing
- Must work with existing read-only architecture

## Goals / Non-Goals

**Goals:**
- Extend scan to any historical date range
- Provide real-time progress feedback
- Handle large result sets efficiently
- Enable digest of current view
- Maintain existing today-only behavior as default

**Non-Goals:**
- Gmail mutations (still read-only)
- Real-time sync (batch/overnight is fine)
- Multi-account support (v1 still single account)

## Decisions

### Decision: Date range specification format

**Chosen:** Flexible format supporting multiple styles:

CLI arguments:
```bash
maily scan --start-date 2024-01-01 --end-date 2024-01-31
maily scan --last 7days
maily scan --this month
maily scan --older-than 30days
```

Config file:
```toml
[scan]
date_range = "last 30 days"
include_read = true
chunk_size = "day"
```

**Rationale:**
- Natural language for common cases
- Explicit dates for precise control
- Config for persistent defaults

### Decision: Date-based chunking default

**Chosen:** Default to day-based chunking with configurable options: day, week, month, year

Chunk sizes:
- `day`: Process one calendar day at a time
- `week`: Process one calendar week (Mon-Sun) at a time  
- `month`: Process one calendar month at a time
- `year`: Process one calendar year at a time

**Rationale:**
- Day: Best progress granularity, good for recent backlogs
- Week: Good balance for 1-2 year backlogs
- Month/Year: For very old emails where progress detail is less important

### Decision: Progress reporting mechanism

**Chosen:** Multi-level progress with configurable verbosity:

Level 1 (default): Overall percentage + current chunk
```
Scanning: 35% complete (Processing: 2024-01-15, 450/1287 emails)
```

Level 2 (verbose): Add rate + ETA
```
Scanning: 35% complete (Processing: 2024-01-15, 450/1287 emails, 120/min, ~6min remaining)
```

Level 3 (debug): Add per-chunk details
```
[2024-01-15] Fetched 45, Classified 45, Cached 12, Time: 2.3s
Scanning: 35% complete...
```

**Rationale:**
- Default is informative without being noisy
- Verbose adds useful ETA info
- Debug for troubleshooting

### Decision: Incremental sync tracking

**Chosen:** Store sync state in database with:
- `last_sync_date`: Last date successfully processed
- `last_sync_email_id`: Last email ID processed (for resumption)
- `total_processed`: Total emails processed in current sync
- `status`: running/completed/failed
- `started_at`: When sync started
- `chunk_size`: Current chunk setting

**Rationale:**
- Resume capability
- Progress tracking across sessions
- Audit trail

### Decision: Virtual scrolling implementation

**Chosen:** Textual's built-in virtual scrolling with custom data source:

- Only render visible nodes + buffer (e.g., 10 above/below)
- Load email details lazily when node comes into view
- Cache loaded email bodies in memory (LRU cache, ~50 emails)

**Rationale:**
- Textual handles this well
- Minimal custom code
- Proven performance

### Decision: Digest current view scope

**Chosen:** Digest applies to currently **visible** emails in TUI (not all in category):

- Respects current filters/sort
- Only analyzes what's on screen (~20-50 emails)
- Cached per view (view = category + filters + sort + scroll position)

**Rationale:**
- Fast (small set)
- Context-aware (what user is looking at)
- Cacheable (same view = same digest)

**Alternative considered:**
- Digest all in category: Slow for large categories, less relevant
- Digest all selected: Requires selection, different use case

### Decision: Memory efficiency for large scans

**Chosen:** Stream-based processing with batch commits:

```
1. Fetch chunk from Gmail (e.g., 1 day)
2. Parse and classify emails in memory
3. Insert into DB in batch
4. Clear memory
5. Repeat for next chunk
```

Batch size: Configurable, default 100 emails
Memory per batch: ~10MB (100 emails * ~100KB average)

**Rationale:**
- Bounded memory usage
- Gmail API returns ~100 at a time anyway
- Atomic batch commits

## Risks / Trade-offs

**[Risk]** Gmail API rate limits could pause long scans → **Mitigation:** Implement exponential backoff, respect quotas, report delays to user

**[Risk]** Very large mailboxes (100K+ emails) could take hours → **Mitigation:** Progress reporting, resumption support, chunk size tuning

**[Risk]** Memory issues with very large individual emails (10MB+ attachments) → **Mitigation:** Limit body size stored, truncate large emails, warn user

**[Risk]** TUI performance with 10K+ emails → **Mitigation:** Virtual scrolling, lazy loading, tested with synthetic large datasets

**[Risk]** Incremental sync complexity (resuming mid-chunk) → **Mitigation:** Checkpoint at chunk boundaries only, don't resume mid-chunk

## Migration Plan

**For existing users:**
- No migration needed
- New config options are optional
- Default behavior unchanged (today only, unread only)

**For new users:**
- Config includes commented examples of historical scan options

**Rollback:**
- Revert to previous version
- New config options ignored by old version

## Open Questions

- Should we support scanning by label/folder in addition to date range? (Future enhancement)
- Should we add a `--dry-run` option to preview scan scope before executing?
- What's the ideal default chunk size for different mailbox sizes?
- Should progress be logged to a file for long-running scans?
