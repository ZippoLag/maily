## 1. install.sh core

- [x] 1.1 Create `install.sh` at repo root with shebang (`#!/usr/bin/env bash`), `set -euo pipefail`, and a `cd "$(dirname "$0")"` to find the repo root; verify the script runs without error on an empty invocation
- [x] 1.2 Implement OS detection (`uname -s`) for Darwin/Linux/WSL and print the detected platform; verify correct output on macOS and Linux
- [x] 1.3 Implement Python detection: try `python3` then `python`, verify version >= 3.11, exit with clear message if missing or too old; verify with Python 3.11+ and with Python 3.10
- [x] 1.4 Implement venv creation at `~/.venv/maily` (skip if already exists, activate if present); verify venv is created and activated correctly
- [x] 1.5 Implement `pip install -e '.[gmail,secure,tui]'` inside the venv; verify maily is importable after install (`python -c "import maily"`)
- [x] 1.6 Add `--pipx` flag to use pipx instead of venv; verify pipx install works when pipx is available
- [x] 1.7 Print success message with next steps (`maily init --oauth-client-file ...` and `maily scan`); verify the message is printed on successful install

## 2. Error handling

- [x] 2.1 Handle missing Python with platform-specific install instructions (brew on macOS, apt on Ubuntu, etc.); verify the error message includes the correct command
- [x] 2.2 Handle Python version too old with suggestion to use pyenv or deadsnakes PPA; verify the error message is clear
- [x] 2.3 Handle pip install failure by printing the pip error and suggesting `--pipx` fallback; verify the error is surfaced

## 3. Documentation

- [x] 3.1 Update README.md installation section to lead with `./install.sh` and keep manual methods as "Advanced" alternatives; verify the README renders correctly
- [x] 3.2 Make `install.sh` executable (`chmod +x`); verify `./install.sh --help` or `./install.sh` runs without "permission denied"