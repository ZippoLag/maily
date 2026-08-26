## Context

Current TUI (`maily/tui.py`) implements read-only browsing with category/email tree structure, but selecting emails does nothing. The original spec requires email detail viewing. Users also need a way to quickly summarize emails.

Constraints: Must work with existing Textual widget system. Summary generation should use inference when available but provide deterministic fallback. Must maintain read-only nature (no Gmail mutations).

## Goals / Non-Goals

**Goals:**
- Enable email detail viewing via expansion
- Add summary hotkey with inference/deterministic fallback
- Maintain existing TUI patterns and keyboard navigation
- Keep the TUI read-only (no mutations)

**Non-Goals:**
- Batch summary operations (deferred to future change)
- Digest of all emails (deferred to future change)
- Gmail mutations from TUI

## Decisions

### Decision: Email expansion mechanism

**Chosen:** Use Textual Tree widget's built-in expand/collapse with custom node content

Implementation:
- Category nodes remain as containers
- Email nodes are leaf nodes that can be expanded
- Expanded email nodes show additional child nodes for sender and body
- Or: Use a single node with dynamic label that updates on expand

**Rationale:**
- Minimal code changes
- Consistent with Textual patterns
- Users already understand tree expansion

**Alternatives considered:**
- Separate detail pane: More complex, requires layout changes
- Modal popup on selection: Disrupts browsing flow

### Decision: Summary hotkey

**Chosen:** 's' key, displayed in footer

**Rationale:**
- 's' for Summary is memorable
- Doesn't conflict with existing bindings ('q', 's' for sort - need to check)
- Standard position in footer

**Note:** Current `tui.py:23` has `("s", "sort", "Sort")` - this would be a conflict. Need to either:
- Use different key (e.g., 'S' uppercase, or 'm' for summarize)
- Remove sort binding (but it's useful)
- Make it contextual (only active when email selected)

**Revised decision:** Use 'S' (uppercase) for summary when email selected, keep 's' for sort when category selected.

### Decision: Summary generation approach

**Chosen:** Two-tier approach:

1. **Inference available and enabled**: Use Ollama with a summary prompt
2. **Inference unavailable or disabled**: Truncate body to first 200 characters with "... (truncated)" indicator

Prompt for inference:
```
Summarize this email in 2-3 sentences. Focus on action items, key information, and sender intent.

Email:
- From: {sender_name} <{sender_email}>
- Subject: {subject}
- Body: {body}

Summary:
```

**Rationale:**
- Graceful degradation
- No LLM dependency for core functionality
- Inference provides better summaries when available

**Alternatives considered:**
- Always require inference: Blocks feature for users without Ollama
- More complex fallback: Overkill for a simple preview

### Decision: Summary caching

**Chosen:** Cache inference-generated summaries in database, keyed by message_id + fingerprint

Fingerprint includes:
- message content
- inference model
- inference settings

**Rationale:**
- Avoid re-generating summaries for same email
- Inference can be expensive/slow
- Deterministic truncation doesn't need caching

**Alternatives considered:**
- No caching: Wastes resources on repeated views
- File-based cache: More complex than SQLite

### Decision: Email expansion content

**Chosen:** Show when expanded:
```
From: {sender_name} <{sender_email}>
Subject: {subject}

{body}
```

**Rationale:**
- Essential information for understanding email
- Matches user request exactly
- Simple to implement

**Alternatives considered:**
- Show only body: Missing sender context
- Show metadata (date, etc.): More clutter, less useful

### Decision: Body formatting

**Chosen:** 
- Wrap text to terminal width
- Preserve line breaks from original
- Limit displayed body to first 1000 characters with "... (show more)" if longer
- Full body available via scrolling

**Rationale:**
- Balance between visibility and clutter
- Prevents overwhelming the display
- Scrolling allows access to full content

## Risks / Trade-offs

**[Risk]** Hotkey conflict with existing 's' for sort → **Mitigation:** Use 'S' (uppercase) or make contextual

**[Risk]** Long email bodies overwhelm the TUI → **Mitigation:** Truncate display with "show more" option

**[Risk]** Inference summaries are slow → **Mitigation:** Cache summaries, show "Generating..." indicator

**[Risk]** Summary prompt may not work well for all email types → **Mitigation:** Accept that inference quality varies, provide fallback

## Migration Plan

**For existing users:**
- No database migration needed (new table for summary cache will be created automatically)
- No config changes needed
- TUI will show new hotkey in footer

**For new users:**
- No special handling needed

**Rollback:**
- Remove 'S' hotkey binding
- Remove summary cache table (optional)
- Revert TUI expansion changes

## Open Questions

- Should the expansion be automatic on selection, or require Enter key? (Proposed: Enter key to toggle)
- Should there be a "show more" option for truncated bodies, or just rely on scrolling?
- Should summaries be persisted to the database for future reference, or only cached for the session?
- What's the ideal summary length when using inference? (Proposed: 2-3 sentences)
