# Design: TUI Reading Pane Layout

## Context

See proposal.md — Why. In `BrowseApp.compose()` the tree `root` and `self.reading_pane` (a `Static`) are yielded in a vertical layout. A `Static` defaulting to `height: 1fr` (or auto-grow on long content) can take the whole screen, hiding the list.

## Goals / Non-Goals

- **Goals**: Reading pane always occupies a fixed bottom height when visible; add a toggle binding so users can reclaim full-screen list height.
- **Non-Goals**: No changes to pane content rendering (that's change 4). No resizable pane.

## Decisions

- **Constrain with a fixed `height` and make the tree `1fr`**: Set `self.reading_pane.styles.height = FIXED_PANE_HEIGHT` (a module constant, e.g. ~12 lines) and `self.reading_pane.styles.max_height = FIXED_PANE_HEIGHT`, and give the tree `height = 1fr` so it expands to fill the space above. The pane's internal content scrolls rather than growing the widget.
- **Toggle binding**: Add a key (e.g. `r` for reading pane / or reuse a sensible binding) invoking `action_toggle_read_pane` that flips `self.reading_pane.display`. When hidden, the tree takes the full height.
- Keep the pane as a `Static`; scrolling comes from wrapping it in a container with its own scroll behavior rather than the Static growing.

## Risks / Trade-offs

- Choosing a specific toggle key is a UI decision → documented in README; convertible later.

## Migration Plan

None required.

## Open Questions

None.