## Why

The current list interaction model conflates "selection" (highlighted email) with "marking" (a checkbox set), exposes an expansion feature (triangles, enter/space to expand) that is useless, and binds several keys (`m`, `Ctrl+A`, `Ctrl+D`, Shift+arrows) to confusing or broken behaviors. This makes triage slower and the mental model ambiguous.

## What Changes

- **Remove the expand feature entirely.** Delete the expand/collapse triangles and the "expand" behavior. Enter and spacebar no longer expand — they now **mark** (toggle the checkbox on) the highlighted email. The `m` key binding is removed.
- **New line format.** Each email line renders as `[ ]` or `[x]`, then the first sender address preceded by `... ` if there is more than one sender, then the subject.
- **Clear selection = marking semantics.** "Selection" means the currently highlighted email. "Marking" is the set of `[x]`-checked emails. Remove all conflation between the two in code and docs.
- **`Ctrl+M` toggles mark/unmark for all emails in the current date** (the same date scope the digest uses), not just those visible in the current scroll. `Ctrl+A` (select all) is removed, and `Ctrl+D` is removed.
- **`c` (edit categories) applies to marked, else selected, else none** — the same fallback logic `S` already uses.
- **`s` (sort) prints a message** explaining the current sorting logic.
- **Shift+arrow bindings removed.**

## Capabilities

### New Capabilities
- `tui/email-line-format`: Email rows render as `[ ]`/`[x]` mark state, truncated sender, then subject.

### Modified Capabilities
- `tui/email-expansion`: The expand/collapse feature is removed entirely; enter/space no longer expand.
- `tui/keyboard-selection`: Key bindings change (`m`, Shift+arrows, `Ctrl+A`, `Ctrl+D` removed; `Ctrl+M` added; enter/space mark; `s` sort discloses its logic).
- `tui/multi-select`: Marking model clarified (selection = highlighted; marking = checkbox set); `c` edit-categories resolves marked → selected → none.

## Impact

- `maily/tui.py` — bindings, render of email rows, mark actions, the `c`/`s` handlers.
- `README.md` — keyboard shortcuts table and interaction documentation.
- Existing keyboard/multi-select/expansion specs get modified.