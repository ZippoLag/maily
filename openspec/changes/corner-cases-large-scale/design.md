## Context

Users with large email backlogs (5000+ unread, 12000+ read) need to triage "email debt" efficiently. The system must handle:
- Very large volumes (10K+ emails)
- Long-running operations (hours)
- Interruptions and resumption
- Memory constraints
- Gmail API rate limits

Constraints:
- Must work within Gmail API quotas (varies by account type)
- Must not exhaust system memory
- Must provide progress visibility
- Must allow resumption after interruption
- AI assistance is optional (fallback to deterministic)

## Goals / Non-Goals

**Goals:**
- Process 10K+ emails in long-running mode
- Provide real-time progress feedback
- Handle Gmail rate limits gracefully
- Memory-efficient processing
- Error resilience (continue on failures)
- AI-assisted bulk suggestions

**Non-Goals:**
- Gmail mutations (delete, archive, mark read) - still read-only suggestions
- Real-time processing (batch/overnight is fine)
- Multi-account support (v1 still single account)

## Decisions

### Decision: Long-running mode architecture

**Chosen:** Extended scan mode with dedicated progress tracking:

```python
# Normal scan (current behavior)
maily scan  # Today's unread, fast

# Long-running scan (new)
maily scan --long-running --start-date 2020-01-01 --include-read
```

Features:
- No timeout on overall scan
- Periodic progress saves (every 100 emails or 5 minutes)
- Progress logging to file
- Graceful interruption handling (Ctrl+C)

**Rationale:**
- Clear separation from normal scan
- Explicit user intent for long operations
- Can be run in background

**Alternatives considered:**
- Background daemon: More complex, requires process management
- Separate command: Less intuitive, more to learn

### Decision: Checkpoint frequency

**Chosen:** Checkpoint every 100 emails OR every 5 minutes, whichever comes first

Configurable via:
```toml
[scan]
checkpoint_interval_emails = 100
checkpoint_interval_seconds = 300
```

**Rationale:**
- 100 emails: Good batch size for Gmail API
- 5 minutes: Ensures progress isn't lost on slow connections
- Configurable: Users can tune based on their setup

### Decision: Progress logging format

**Chosen:** JSON Lines format for progress logs:

```json
{"timestamp": "2024-01-15T10:30:00Z", "event": "batch_start", "batch": 5, "emails_total": 5000}
{"timestamp": "2024-01-15T10:30:15Z", "event": "email_processed", "email_id": "12345", "index": 450}
{"timestamp": "2024-01-15T10:30:15Z", "event": "batch_complete", "batch": 5, "duration_seconds": 15.2}
```

**Rationale:**
- JSON Lines: Easy to parse, append-only
- Structured: Machine-readable for analysis
- Human-readable: Can be viewed directly

**Alternatives considered:**
- Plain text: Less structured, harder to parse
- CSV: Less flexible for nested data

### Decision: Suggestion grouping strategy

**Chosen:** Hierarchical grouping for bulk suggestions:

```
Level 1: By sender domain (highest priority)
  ├─ newsletter@example.com (500 emails)
  │   ├─ Suggest: Delete (confidence: high)
  │   └─ Suggest: Add Newsletters category (confidence: high)
  └─ notifications@service.com (300 emails)
      └─ Suggest: Archive (confidence: medium)

Level 2: By subject patterns
  ├─ "Your invoice #" (200 emails)
  │   └─ Suggest: Add Work category (confidence: medium)
  └─ "Weekly digest" (150 emails)
      └─ Suggest: Add Newsletters category (confidence: high)

Level 3: By existing categories
  └─ Already categorized as "Other" (100 emails)
      └─ Suggest: Review for new category (confidence: low)
```

**Rationale:**
- Sender domain: Most actionable (delete/archive decisions)
- Subject patterns: Good for categorization
- Existing categories: Identifies miscategorized emails

### Decision: Confidence calculation for bulk

**Chosen:** Weighted scoring:

```python
def bulk_confidence(group_emails: list[EmailMessage], all_emails: list[EmailMessage]) -> float:
    same_sender_score = count_same_sender(group_emails) / len(group_emails) * 0.4
    same_domain_score = count_same_domain(group_emails) / len(group_emails) * 0.3
    same_subject_pattern_score = count_subject_pattern(group_emails) / len(group_emails) * 0.2
    group_size_score = min(len(group_emails) / len(all_emails), 0.1)  # Cap at 10%
    
    base_score = same_sender_score + same_domain_score + same_subject_pattern_score + group_size_score
    
    # Bonus for known patterns
    if all have "unsubscribe" in body:
        base_score += 0.1  # Newsletter pattern
    if all from same automated system:
        base_score += 0.1  # Notification pattern
    
    return min(base_score, 1.0)
```

Buckets:
- **High**: 0.7-1.0 (Strong pattern, large group)
- **Medium**: 0.4-0.7 (Moderate pattern)
- **Low**: 0.0-0.4 (Weak or uncertain pattern)

**Rationale:**
- Group consistency is primary factor
- Known patterns get bonuses
- Large groups relative to total get slight boost (more impact)

### Decision: Error handling strategy

**Chosen:** Continue on all non-fatal errors, aggregate at end:

| Error Type | Behavior |
|------------|----------|
| Network timeout | Retry with backoff, continue after max retries |
| Rate limit (429) | Pause with backoff, continue |
| Quota exceeded | Pause, save state, report to user |
| Parse error (single email) | Log, skip to next |
| DB error | Rollback batch, stop scan |
| Memory error | Save state, exit with error |

**Rationale:**
- Maximize email processed
- Transient errors: Retry and continue
- Fatal errors: Stop with clear message
- Partial success: Better than none

### Decision: Memory management strategy

**Chosen:** Multi-layer caching with LRU eviction:

```
L1 Cache (In-memory, hot data):
- EmailMessage objects for current batch: ~100 emails
- Email bodies being viewed in TUI: ~50 bodies (LRU)
- Classification results: All (needed for display)

L2 Cache (Disk, warm data):
- Recently processed batches: Last 5 batches
- Can be reloaded if needed

L3 Storage (Database, cold data):
- All historical data
- Loaded on demand
```

Memory budget:
- Default: 256MB max for maily process
- Configurable: memory_limit_mb in config.toml

**Rationale:**
- Hot data in memory for performance
- Warm data on disk for quick reload
- Cold data in DB for persistence
- Configurable limits for different systems

### Decision: Suggestion intent storage

**Chosen:** Store mutation intents in database for future execution:

```sql
CREATE TABLE mutation_intents (
    id INTEGER PRIMARY KEY,
    intent_type TEXT NOT NULL,  -- 'delete', 'archive', 'mark_read'
    message_ids TEXT NOT NULL,  -- JSON array
    created_at TEXT NOT NULL,
    executed_at TEXT,
    status TEXT NOT NULL  -- 'pending', 'executed', 'failed'
);
```

**Rationale:**
- Persistent across sessions
- Can be executed when mutation support is added
- Audit trail of intended actions
- Can be reviewed/edited before execution

### Decision: Progress notification mechanism

**Chosen:** Multiple notification channels:

1. **CLI**: Print to stdout
2. **TUI**: Status bar + notification widget
3. **Log file**: Structured JSON Lines to ~/.maily/logs/scan_progress.log
4. **Desktop notification** (optional): System notification on completion

**Rationale:**
- CLI: Simple, always works
- TUI: Visual feedback for interactive use
- Log file: Persistent record for review
- Desktop: Convenient for background runs

## Risks / Trade-offs

**[Risk]** Long-running scans could conflict with normal usage → **Mitigation:** Lock file to prevent concurrent scans, clear error if scan already running

**[Risk]** Gmail API quota could be exhausted mid-scan → **Mitigation:** Track quota usage, pause when approaching limits, auto-resume

**[Risk]** Memory issues with very large individual emails → **Mitigation:** Limit email body size stored, truncate large attachments, warn user

**[Risk]** Suggestion quality for diverse email sets → **Mitigation:** Group-based suggestions, confidence scoring, user review required

**[Risk]** Progress log files could grow large → **Mitigation:** Rotate log files by date, limit size, compress old logs

**[Risk]** Checkpoint overhead for very frequent saves → **Mitigation:** Batching (every 100 emails or 5 min), async writes

## Migration Plan

**For existing users:**
- No migration needed
- New features are opt-in
- Default behavior unchanged

**For new users:**
- All features available from start

**Rollback:**
- Revert to previous version
- New tables ignored by old version
- Log files remain but unused

## Open Questions

- Should long-running mode be the default for historical scans? (Proposed: Yes, with timeout override)
- Should we support pausing and resuming scans manually? (Proposed: Yes, via CLI command)
- What's the ideal checkpoint frequency for different systems? (Proposed: Configurable)
- Should suggestion intents be exportable/importable for sharing? (Future enhancement)
- Should we add a "preview" mode that shows what would be scanned without fetching?
- Should long-running scans be runnable as a background service/daemon? (Future enhancement)
