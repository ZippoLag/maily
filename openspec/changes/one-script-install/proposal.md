## Why

The current installation process requires users to manually choose between three methods (venv, pipx, system-wide), handle platform-specific quirks like PEP 668 on macOS Homebrew Python, and know which extras to install. A single `install.sh` script that auto-detects the OS and picks the best installation method removes this friction and makes the first-run experience consistent across Linux, macOS, and WSL.

## What Changes

- **New**: `install.sh` at the repo root — a single bash entry point that detects the OS, checks for Python 3.11+, selects the appropriate installation method (venv preferred, pipx fallback), installs maily with all extras, and optionally runs `maily init`
- **Modified**: README.md installation section — replace the three manual methods with a single `curl | bash` or `./install.sh` instruction, keeping manual methods as advanced alternatives

## Capabilities

### New Capabilities

(none — this is a tooling-only change with no spec-level behavior modifications)

### Modified Capabilities

(none)

## Impact

- **New file**: `install.sh` at repo root
- **Modified file**: `README.md` (installation instructions section)
- **No code changes**: The maily Python package itself is unchanged
- **No dependency changes**: Same Python and pip requirements
