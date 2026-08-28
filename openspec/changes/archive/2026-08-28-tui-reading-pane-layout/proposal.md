## Why

The reading/preview pane at the bottom of the screen sometimes takes over the whole screen, disrupting the email list view. It should occupy a fixed height at the bottom whenever it is visible.

## What Changes

- The reading pane (preview pane) always occupies a **fixed height at the bottom** of the screen when visible, and never the whole screen.
- Add a way to show/hide the pane and a key binding to toggle it, so the whole-screen case becomes impossible and the user retains control.

## Capabilities

### New Capabilities
- `tui/reading-pane-layout`: The preview pane occupies a fixed height at the bottom when visible and can be toggled.

## Impact

- `maily/tui.py` — the compose/reading pane layout and its toggle action.
- `README.md` — shortcut table addition if a binding is added.