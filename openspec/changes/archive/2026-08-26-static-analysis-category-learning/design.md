## Context

Current state: maily has hardcoded static analysis rules in `classifier.py` covering only 3 of 8 categories. Users cannot customize rules. The TUI is read-only. There's no mechanism for learning from user corrections.

Constraints: Must work without LLM inference. Must use TOML for configuration. Must use existing Textual TUI framework. Must maintain backward compatibility with existing database schema.

## Goals / Non-Goals

**Goals:**
- Enable pure static-analysis categorization with comprehensive coverage
- Allow users to define custom rules in config.toml
- Enable TUI-based category editing
- Implement deterministic rule learning from user corrections
- Display multi-category assignments clearly
- Maintain zero LLM dependency for core functionality

**Non-Goals:**
- Semantic/ML-based classification (staying with regex pattern matching)
- Real-time rule application during TUI browsing (rules apply on next scan)
- Cloud sync of user rules or suggestions
- Automated contribution of user rules back to repo (manual process)

## Decisions

### Decision: Rule configuration format

**Chosen:** TOML table of lists under `[classification.rules]`

```toml
[classification.rules]
Action_Required = ["verify", "verification code", "expires", "due date", "payment required"]
Personal = ["mom", "dad", "family", "friend"]
```

**Rationale:** 
- Matches existing TOML config format
- Simple and human-editable
- Easy to validate on load
- Mirrors the internal Rule dataclass structure

**Alternatives considered:**
- Separate rules.toml file: More complex file management
- JSON format: Less human-friendly, not consistent with config
- Inline regex strings with modifiers: Too complex for users

### Decision: Rule matching fields

**Chosen:** Keep default fields (subject, body, sender_email) but make them configurable per rule

```python
Rule(category, patterns, fields=("subject", "body", "sender_email"))
```

**Rationale:**
- Most patterns work across these fields
- Some users may want sender-domain-only rules
- Minimal performance impact

**Alternatives considered:**
- Fixed fields only: Less flexible
- All fields always: Performance overhead for unused fields

### Decision: Rule learning algorithm

**Chosen:** Deterministic frequency-based pattern extraction with stop word filtering

Algorithm:
1. For each category, collect all emails user has assigned to it
2. Extract all words (split on non-alphanumeric) from subject + body
3. Filter out stop words (English, ~100 words)
4. Count frequency of each remaining word across emails in category
5. Suggest words appearing in >=N emails (configurable threshold, default: 3)
6. Present suggestions to user for confirmation

**Rationale:**
- No LLM required
- Deterministic and reproducible
- Simple to implement and understand
- Works offline

**Alternatives considered:**
- N-gram extraction: More complex, marginal benefit
- TF-IDF weighting: Overkill for this use case
- LLM-based suggestion: Violates no-LLM requirement

### Decision: Primary category selection

**Chosen:** First matched rule determines primary, user overrides take absolute priority

Order of precedence:
1. User-assigned categories (first one is primary)
2. Rule-matched categories (first rule to match is primary)
3. Fallback to "Other"

**Rationale:**
- Deterministic and predictable
- Respects user intent over automated classification
- Simple to implement

**Alternatives considered:**
- Most specific category first: Requires category hierarchy definition
- User preference ordering: More configuration complexity

### Decision: TUI category editing flow

**Chosen:** Modal dialog with checkbox list

Flow:
1. User presses 'c' on selected email(s)
2. Modal opens showing all categories with checkboxes
3. User toggles checkboxes to add/remove categories
4. User presses 's' to save or 'Esc' to cancel
5. On save: persist to database, close modal, refresh display

**Rationale:**
- Consistent with Textual app patterns
- Works with keyboard only
- Clear visual feedback

**Alternatives considered:**
- Type-ahead category selection: More complex, less discoverable
- Separate screen for category management: Disrupts browsing flow

### Decision: Database schema for new data

**Chosen:** Two new tables with foreign keys to messages

```sql
CREATE TABLE user_category_overrides (
    message_id TEXT PRIMARY KEY REFERENCES messages(id),
    categories TEXT NOT NULL,  -- JSON array of category names
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE learned_rule_suggestions (
    id INTEGER PRIMARY KEY,
    pattern TEXT NOT NULL,
    category TEXT NOT NULL,
    source_message_id TEXT REFERENCES messages(id),
    confidence REAL NOT NULL,  -- 0-1 based on frequency
    status TEXT NOT NULL,  -- 'pending', 'accepted', 'rejected'
    created_at TEXT NOT NULL
);
```

**Rationale:**
- Normalized design
- Tracks provenance of suggestions
- Allows for future features (e.g., dismissing suggestions)

**Alternatives considered:**
- Single table with nullable fields: Less clear schema
- JSON column in existing table: Harder to query and index

### Decision: When to apply user overrides

**Chosen:** Overrides are applied after classification, replacing rule-based categories entirely

Flow:
1. Run classification (rules + inference) → get categories
2. Check for user override for message_id
3. If override exists, use override categories instead
4. Store both original and override in database

**Rationale:**
- User intent takes absolute priority
- Original classification preserved for reference
- Simple logic

**Alternatives considered:**
- Merge override with classification: Confusing semantics
- Override only specified categories: More complex, less clear intent

## Risks / Trade-offs

**[Risk]** User creates conflicting rules that match the same email to multiple categories → **Mitigation:** This is actually desired behavior (multi-category is supported). Will document that order matters.

**[Risk]** Rule learning suggests noisy or overly-specific patterns → **Mitigation:** Use minimum threshold (3+ emails), filter stop words, require user confirmation before activation.

**[Risk]** Performance degradation with many user rules → **Mitigation:** Compile regex patterns once at load time, cache compiled patterns. With <100 patterns, impact should be negligible.

**[Risk]** TUI becomes cluttered with too many category badges → **Mitigation:** Truncate display with "+N more" indicator, show full list on hover/focus.

**[Risk]** Database migration complexity for existing users → **Mitigation:** Use SQLite's `CREATE TABLE IF NOT EXISTS` for new tables. Existing users get new tables automatically on first run.

**[Risk]** Config file errors prevent maily from starting → **Mitigation:** Validate config on load, provide clear error messages, keep last-known-good config backup.

## Migration Plan

**For existing users:**
1. New tables created automatically on first run (no migration needed)
2. No existing data modified
3. Default rules remain unchanged
4. User rules section in config.toml is optional

**For new users:**
1. Default config includes commented-out examples of user rules
2. Default rules work out of the box
3. No action required

**Rollback:**
- Delete new tables from database
- Remove user rules from config.toml
- Revert to previous version

## Open Questions

- What should the minimum threshold be for rule suggestions? (Proposed: 3 emails with same pattern → suggest rule)
- Should rule suggestions be auto-applied after N confirmations, or always require manual action?
- How to handle case where user rule pattern matches no emails after being added? (Show warning? Auto-remove?)
- Should there be a maximum number of user rules to prevent performance issues?
