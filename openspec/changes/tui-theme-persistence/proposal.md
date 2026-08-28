## Why

The Textual color theme can be switched at runtime (e.g. `Ctrl+T`), but the selection is lost on close. The user's chosen theme should persist across restarts via the settings file.

## What Changes

- Persist the selected Textual theme in the maily settings file.
- On startup, apply the persisted theme; on theme change, write it back.
- Expose the theme option in the config defaults.

## Capabilities

### New Capabilities
- `tui/theme-persistence`: The selected theme is persisted and restored across restarts.

### Modified Capabilities
- `local-state`: the persisted configuration gains a theme setting; defaults document it.

## Impact

- `maily/config.py` — theme setting and default template documentation.
- `maily/tui.py` — apply persisted theme on mount; persist on change.
- New spec `tui/theme-persistence`.