## Context

Current TUI is read-only with no multi-select. Users with large backlogs (5000+ unread) need to perform batch operations efficiently. Gmail labels can provide useful context for identifying patterns.

Constraints:
- Must maintain read-only safety (no Gmail mutations in this change)
- Must work with existing Textual framework
- AI suggestions are optional (fallback to deterministic)
- Must integrate with existing category system

## Goals / Non-Goals

**Goals:**
- Enable multi-select in TUI
- Enable batch categorization
- Display Gmail labels as badges
- Provide AI-assisted batch action suggestions
- Maintain existing single-email editing

**Non-Goals:**
- Gmail mutations (delete, archive, mark read) - will be separate future change
- Real-time suggestion updates
- Bulk export/import of selections

## Decisions

### Decision: Multi-select interaction model

**Chosen:** Space to toggle, Ctrl+A for select all, Ctrl+D for deselect all

Behavior:
- **Space**: Toggle email selection
- **Ctrl+A**: Select all visible emails
- **Ctrl+D**: Deselect all
- **Shift+Arrow**: Range select (future enhancement)
- **Escape**: Clear selection

**Rationale:**
- Space is standard for toggle in many apps
- Ctrl+A/D are intuitive
- Doesn't conflict with existing bindings

**Existing bindings to check:**
- Current: 'q' quit, 's' sort
- Proposed: 'c' for category (contextual), Space for select

### Decision: Selection persistence model

**Chosen:** Persist by message_id, not by position

Selection is stored as a set of message_ids. When view changes (sort, filter), the same message_ids remain selected even if their position changes.

**Rationale:**
- More intuitive (user thinks "these emails" not "these positions")
- Works with sorting/filtering
- Can be persisted across sessions if needed

**Alternatives considered:**
- Position-based: Breaks with sorting, less intuitive
- Both: More complex

### Decision: Gmail label storage

**Chosen:** Add `labels: list[str]` field to EmailMessage model

```python
@dataclass(frozen=True)
class EmailMessage:
    # ... existing fields
    labels: tuple[str, ...] = ()  # Gmail label names
```

**Rationale:**
- Minimal change to existing model
- Labels are immutable (frozen dataclass)
- Easy to extend Gmail client to populate

**Alternatives considered:**
- Separate labels table in DB: More complex, labels already in message
- JSON field: Less type-safe

### Decision: Label badge display

**Chosen:** Compact text badges with color coding:

```
[IMPORTANT] [Work] [Newsletters] sender: subject
```

Styling:
- System labels: Standard colors (IMPORTANT=yellow, STARRED=star symbol, etc.)
- Custom labels: Use Gmail's color if available, otherwise cycle through predefined palette
- Truncation: Show first 3-5 labels, then "+2 more" if more exist

**Rationale:**
- Compact and scannable
- Color helps visual parsing
- Truncation prevents clutter

### Decision: Batch categorization flow

**Chosen:**
1. User selects emails (Space)
2. User presses 'c' (category hotkey)
3. Category selection modal opens (same as single-email but with selection count)
4. User toggles categories
5. User confirms
6. Categories applied to all selected emails
7. Notification shows result

**Rationale:**
- Reuses existing category modal
- Contextual hotkey (works for single or multi-select)
- Clear user flow

### Decision: Suggestion generation approach

**Chosen:** Two-tier approach:

**Deterministic (always available):**
- Group by sender domain → suggest categorize or delete
- Group by subject keywords → suggest categorize
- Group by existing categories → suggest similar
- All from same sender → high confidence
- Most from same sender → medium confidence

**Inference (when available):**
- Analyze content for semantic patterns
- Identify email types (receipts, newsletters, notifications)
- Suggest based on user's historical categorization patterns

**Rationale:**
- Graceful degradation
- Deterministic provides baseline functionality
- Inference adds value when available

### Decision: Suggestion confidence calculation

**Chosen:** Simple scoring system:

```python
def calculate_confidence(selected_emails: list[EmailMessage]) -> float:
    # Same sender: +0.4
    # Same domain: +0.3
    # Same subject prefix: +0.2
    # Same existing category: +0.1
    # Pattern match (e.g., all have "unsubscribe"): +0.3
    # Count: more emails = higher confidence (cap at 0.2)
    
    score = 0.0
    # ... calculate components
    return min(score, 1.0)
```

Buckets:
- **High**: 0.7-1.0
- **Medium**: 0.4-0.7
- **Low**: 0.0-0.4

**Rationale:**
- Transparent and adjustable
- Easy to understand
- Can be extended with more patterns

### Decision: Suggestion caching

**Chosen:** Cache suggestions per selection (set of message_ids)

Cache key: sorted tuple of selected message_ids
Cache invalidation: when selection changes

**Rationale:**
- Avoids recomputing on every keystroke
- Simple invalidation
- Small cache size (only for current selection)

### Decision: Read-only safety for suggestions

**Chosen:** For now, only **categorization** suggestions are actionable. Other suggestions (delete, archive, mark read) are displayed but require future mutation support.

Current behavior:
- **Add/Remove category**: Applied immediately (stored in DB)
- **Delete/Archive/Mark Read**: Displayed but not actionable, with note "Requires write access"

**Rationale:**
- Maintains read-only safety
- Shows users what's possible in future
- Categorization is most immediately useful

## Risks / Trade-offs

**[Risk]** Multi-select conflicts with existing 's' sort binding → **Mitigation:** Use Space for select, keep 's' for sort, 'c' is contextual

**[Risk]** Performance with 10K selected emails → **Mitigation:** Warn user before batch operations on large selections, chunk the operations

**[Risk]** Suggestion quality varies → **Mitigation:** Show confidence levels, allow user to ignore, deterministic fallback

**[Risk]** Gmail label colors not available → **Mitigation:** Use predefined palette, Gmail API may not expose colors anyway

**[Risk]** Selection state complexity → **Mitigation:** Simple set of message_ids, clear persistence rules

## Migration Plan

**For existing users:**
- No migration needed
- New features are additive
- Existing behavior unchanged

**For new users:**
- Multi-select available from start
- Label badges visible by default

**Rollback:**
- Revert TUI changes
- Remove labels field from EmailMessage (need migration)

## Open Questions

- Should we support range selection (Shift+click to select all between two emails)?
- Should label badges be clickable to filter by that label?
- Should we persist selection across TUI sessions?
- What's the maximum selection size before warning user? (Proposed: 100)
- Should suggestions be persisted across sessions for the same selection?
- How to display that a suggestion requires write access (vs. can be applied now)?
