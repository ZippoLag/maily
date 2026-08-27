## Context

maily currently documents three installation methods (venv, pipx, system-wide) in the README. Users must choose the right one for their OS and Python setup, handle PEP 668 restrictions on macOS Homebrew Python, and remember the correct extras (`gmail,secure,tui`). The project uses `pyproject.toml` with setuptools and has no compiled extensions — installation is pure Python.

## Goals / Non-Goals

**Goals:**
- Single `./install.sh` that works on Linux, macOS, and WSL without user intervention
- Auto-detect OS and Python version, pick the best installation method
- Handle common failure modes (missing Python, PEP 668, missing pip) with clear messages
- Install maily with all extras in one step
- Optionally run `maily init` at the end

**Non-Goals:**
- Installing system dependencies (Ollama, etc.) — out of scope per user decision
- Windows native support (cmd.exe/PowerShell) — WSL is the supported path
- Uninstall or upgrade logic — separate concern
- Docker or containerized installation

## Decisions

### 1. Installation method: venv preferred, pipx fallback

**Decision**: Create a venv at `~/.venv/maily` by default. Fall back to `pipx` if the user passes `--pipx` or if venv creation fails.

**Rationale**: venv is the most universal method and doesn't require installing pipx first. pipx is better for CLI-only isolation but requires an extra install step on most systems.

**Alternatives considered**:
- pipx-only: Requires `brew install pipx` or `pip install --user pipx` first, adding a chicken-and-egg problem
- System-wide: Breaks on macOS Homebrew Python (PEP 668) and conflicts with system packages

### 2. OS detection via `uname`

**Decision**: Use `uname -s` to detect Darwin (macOS) vs Linux. Check `/proc/version` for Microsoft (WSL). No native Windows support.

**Rationale**: `uname` is available on all POSIX systems and is the standard way to detect OS in bash scripts. WSL reports as Linux but with a Microsoft kernel signature.

### 3. Python version check

**Decision**: Try `python3` first, then `python`. Require 3.11+. Exit with a clear message if not found or too old.

**Rationale**: Some systems have `python3` but not `python`, or vice versa. Version 3.11 is the minimum per `pyproject.toml`.

### 4. Script location and distribution

**Decision**: Place `install.sh` at the repo root. Users clone the repo and run `./install.sh`, or download it directly.

**Rationale**: Keeps it simple and visible. No need for a separate distribution mechanism for a v1 project.

### 5. Idempotent design

**Decision**: If `~/.venv/maily` already exists, activate it and run `pip install -e '.[gmail,secure,tui]'` to update. Don't recreate the venv.

**Rationale**: Users will re-run the script to update. Recreating the venv would lose installed packages and is slower.

## Risks / Trade-offs

- [User doesn't have `python3` installed] → Script exits with a clear message and platform-specific install instructions (e.g., `brew install python3` on macOS, `sudo apt install python3` on Ubuntu)
- [User has Python but it's too old] → Script detects version and suggests pyenv or deadsnakes PPA
- [Network issues during pip install] → pip handles retries internally; script exits with the pip error message
- [User runs from a directory that isn't the repo root] → Script uses `cd "$(dirname "$0")"` to find the repo root
