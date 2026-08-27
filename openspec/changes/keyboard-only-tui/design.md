## Context

The TUI uses Textual's `Tree` widget for email browsing. Currently, `on_tree_node_selected` (fires on click or explicit selection) sets `self.selected_email`. Actions like `action_summarize` and `action_mark` check `self.selected_email` and show "Select an email first" if it's `None`. Keyboard navigation (arrow keys) highlights nodes via `Tree.NodeHighlighted` but does NOT trigger `NodeSelected`, so the focused email is never registered as the active selection.

The `Tree` widget also has a `cursor_line` property that tracks which line the cursor is on. This can be used as a fallback when `NodeHighlighted` is not available or as a complementary mechanism.

## Goals / Non-Goals

**Goals:**
- Make the TUI fully usable via keyboard without mouse interaction
- Focused/highlighted email is treated as the implicit selection
- Actions execute on the focused email or all marked emails
- Preserve existing mouse-driven workflow (click still works)

**Non-Goals:**
- Multi-select via Shift+Arrow (planned in batch-actions change)
- Changing the visual tree layout or widget structure
- Adding new key bindings beyond what's needed for implicit selection

## Decisions

### Decision: Use `Tree.NodeHighlighted` event for implicit selection

**Chosen:** Listen to `Tree.NodeHighlighted` to update `self.selected_email` whenever the user navigates to a new email.

**Rationale:**
- `NodeHighlighted` fires on keyboard navigation (arrow keys, Page Up/Down, Home/End)
- It also fires on mouse hover, which is consistent behavior
- This is the canonical Textual event for "user is looking at this node"
- `cursor_line` is a lower-level property that requires polling; events are cleaner

**Alternatives considered:**
- Polling `tree.cursor_line` on every keypress: More fragile, misses mouse navigation
- Only using `NodeSelected`: Requires explicit selection (click), defeats the purpose
- Adding a new key binding to "focus" an email: Adds unnecessary cognitive overhead

### Decision: Keep `on_tree_node_selected` for backward compatibility

**Chosen:** Keep the existing `on_tree_node_selected` handler but also update `selected_email` in `on_tree_node_highlighted`.

**Rationale:**
- `NodeSelected` still fires on click (mouse or Enter key), so both paths set the same state
- No behavioral change for existing mouse users
- The `selected_email` state is consistent regardless of how the user navigated

### Decision: Bulk actions use marked set, single actions use focused email

**Chosen:** When emails are marked (via 'm'), actions apply to all marked emails. When no emails are marked, actions apply to the currently focused email.

**Rationale:**
- Preserves the existing mark-based batch workflow
- Adds single-email keyboard shortcut workflow without conflict
- Clear mental model: "marked = batch target, focused = single target"

**Alternatives considered:**
- Always apply to marked emails only: Breaks single-email workflow
- Always apply to focused email: Breaks batch workflow
- Apply to both marked + focused: Confusing, duplicates work

### Decision: Status bar reflects current state

**Chosen:** Status bar shows either "N marked | focused: sender - subject" or "focused: sender - subject" depending on whether emails are marked.

**Rationale:**
- Provides immediate feedback on what action will target
- Helps users understand the implicit selection model

## Risks / Trade-offs

**[Risk]** Users may not realize the focused email is "selected" → **Mitigation:** Status bar clearly shows which email is focused; actions immediately work on it

**[Risk]** `NodeHighlighted` may fire too frequently during rapid scrolling → **Mitigation:** Textual debounces this internally; actions are user-initiated so no performance concern

**[Risk]** Conflict with batch-actions change's Space-to-toggle behavior → **Mitigation:** This change is additive; Space toggle still works for explicit multi-select. Implicit selection is the baseline, explicit selection overrides it

## Migration Plan

**For existing users:**
- No migration needed
- Mouse workflow unchanged
- Keyboard shortcuts now "just work" without explicit selection

**Rollback:**
- Remove `on_tree_node_highlighted` handler
- Revert `action_summarize`, `action_mark`, `action_edit_categories` to check `selected_email` only
