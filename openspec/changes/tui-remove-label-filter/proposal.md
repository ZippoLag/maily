## Why

The `l` key binding for filtering by label does nothing. It is dead, misleading functionality and should be removed so the keyboard map is honest.

## What Changes

- **Remove the `l` label-filter binding** and any underlying handler that is non-functional. **BREAKING.**
- Update docs to drop the `l` entry.

## Capabilities

### New Capabilities
_None._

### Modified Capabilities
- `tui/keyboard-selection`: Remove the non-functional `l` filter-by-label binding.

## Impact

- `maily/tui.py` — remove the `l` binding and dead handler.
- `README.md` — shortcut table.