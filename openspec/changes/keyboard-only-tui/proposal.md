## Why

The TUI currently requires mouse interaction to select emails before performing actions. When using keyboard navigation only, pressing 'S' (Summarize) or 'm' (Mark) on a focused email yields "Select an email first" — the highlighted email under the cursor is not treated as the active selection. This makes the TUI unusable without a mouse for common workflows like triage and summarization.

## What Changes

- **Modified**: The focused/highlighted email in the tree is now treated as the implicit selection for single-email actions (Summarize, Mark, Edit Categories)
- **Modified**: Actions like Summarize and Mark work directly on the currently focused email without requiring an explicit mouse click or Space toggle
- **Modified**: Bulk actions (Summarize, Mark) auto-apply to all marked emails when one or more are marked
- **Modified**: The `on_tree_node_selected` handler sets the focused email as the active selection immediately
- **New**: Keyboard-driven action flow: navigate to email → press action key → action executes on that email

## Capabilities

### New Capabilities

- `tui/keyboard-selection`: Focused/highlighted email is implicitly selected for actions; actions execute on the focused email or all marked emails

### Modified Capabilities

_(none — this is new behavior layered on existing TUI)_

## Impact

**Affected code:**
- `maily/tui.py` — Modify `action_summarize`, `action_mark`, `action_edit_categories` to use focused email; update `on_tree_node_selected` behavior
- `tests/test_tui_app.py` — Update tests for keyboard-driven action behavior

**Dependencies:**
- Depends on Textual's `Tree.NodeHighlighted` event (fires on keyboard navigation, not just click)
- No new external dependencies
