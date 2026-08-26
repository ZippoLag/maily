## Why

The current TUI (`maily/tui.py`) does nothing when users navigate and try to expand an email. The original spec requires the ability to review email details. This change adds basic email detail viewing and a summary hotkey to address immediate TUI usability gaps.

This is a **prerequisite** for the deferred `spam-handling-workflow` change, as it establishes the pattern for interactive TUI features.

## What Changes

- **New**: Email expansion in TUI shows sender and body when user navigates to an email
- **New**: Summary hotkey ('s') for currently selected email - uses inference if enabled, otherwise shows a deterministic summary
- **New**: Visual indication of expanded state
- **New**: Database table for storing user-generated summaries (when created via inference)

## Capabilities

### New Capabilities
- `tui/email-expansion`: Expand email nodes to show sender and body content
- `tui/email-summary`: Hotkey to generate/show summary for selected email

### Modified Capabilities
- `email-presentation`: Extended to include email detail display in TUI

## Impact

**Affected code:**
- `maily/tui.py` - Add expansion handling, summary hotkey, modal for summary display
- `maily/db.py` - Add table for user summaries (optional, if persisting)
- `maily/classifier.py` or new module - Summary generation logic

**Dependencies:**
- For inference-based summaries: Ollama (optional, fallback to deterministic)
- Textual framework (already a dependency)

## Relation to Other Changes

This change **unblocks** the deferred `spam-handling-workflow` change by:
1. Establishing interactive TUI patterns (expansion, hotkeys)
2. Proving the TUI can handle user-initiated actions
3. Providing a foundation for more complex TUI features

## Future Work

After this change is complete, a separate `summarize-all` or `digest` change can be created to:
- Summarize all emails in current view
- Generate daily digest
- Batch summary operations
