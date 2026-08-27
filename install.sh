#!/usr/bin/env bash
# maily single-script installer.
#
# Detects the OS, checks for Python 3.11+, and installs maily with all extras
# using a virtual environment (preferred) or pipx (fallback / --pipx).
#
# Usage:
#   ./install.sh            # create/use ~/.venv/maily and pip install -e
#   ./install.sh --pipx     # install via pipx instead of a venv
#   ./install.sh --dry-run  # print what would happen, change nothing
#   ./install.sh --help     # show options and exit

set -euo pipefail

cd "$(dirname "$0")"

DRY_RUN=0
USE_PIPX=0
declare -a EXTRA_ARGS=()

usage() {
  cat <<'EOF'
maily installer

Options:
  --pipx       Install via pipx instead of creating ~/.venv/maily
  --dry-run    Print what the installer would do without changing anything
  --help       Show this help and exit
EOF
}

for arg in "$@"; do
  case "$arg" in
    --pipx) USE_PIPX=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --help) usage; exit 0 ;;
    *) EXTRA_ARGS+=("$arg") ;;
  esac
done

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '  [dry-run] %s\n' "$*"
    return 0
  fi
  "$@"
}

# --- 1.2 OS detection -------------------------------------------------------
detect_platform() {
  local kernel
  kernel="$(uname -s)"
  case "$kernel" in
    Darwin)
      echo "darwin"
      ;;
    Linux)
      # WSL kernels carry "microsoft" or "Microsoft" in the version string.
      if uname -r | grep -qi microsoft; then
        echo "wsl"
      else
        echo "linux"
      fi
      ;;
    *)
      echo "unknown"
      ;;
  esac
}

PLATFORM="$(detect_platform)"
printf 'Detected platform: %s\n' "$PLATFORM"
if [[ "$PLATFORM" == "unknown" ]]; then
  cat <<'EOF'
maily currently supports Linux, macOS (Darwin), and WSL. Your platform was
not recognized. Please follow the manual installation instructions in the
README instead.
EOF
  exit 1
fi

# --- 1.3 Python detection ---------------------------------------------------
find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
  elif command -v python >/dev/null 2>&1; then
    echo "python"
  else
    echo ""
  fi
}

PYTHON_BIN="$(find_python)"

if [[ -z "$PYTHON_BIN" ]]; then
  printf 'Python was not found.\n'
  cat <<'EOF'
maily requires Python 3.11 or newer, but no python3 or python interpreter was
found on your PATH. Install Python and then re-run this installer:
  - macOS:      brew install python@3.12
  - Ubuntu/Debian: sudo apt-get update && sudo apt-get install python3.12
  - Fedora:     sudo dnf install python3
  - Windows/WSL: sudo apt-get update && sudo apt-get install python3.12
EOF
  exit 1
fi

printf 'Using Python: %s (%s)\n' "$PYTHON_BIN" "$(command -v "$PYTHON_BIN")"

PYTHON_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="${PYTHON_VERSION%%.*}"
PY_MINOR="${PYTHON_VERSION#*.}"
PY_MINOR="${PY_MINOR%%.*}"

if [[ "$PY_MAJOR" -lt 3 ]] || { [[ "$PY_MAJOR" -eq 3 ]] && [[ "$PY_MINOR" -lt 11 ]]; }; then
  printf 'maily requires Python 3.11 or newer; you have %s.\n' "$PYTHON_VERSION"
  cat <<'EOF'
Your Python is too old. Options:
  - Use pyenv (https://github.com/pyenv/pyenv) to install Python 3.11+.
  - On Ubuntu/Debian use the deadsnakes PPA:
        sudo add-apt-repository ppa:deadsnakes/ppa
        sudo apt-get update
        sudo apt-get install python3.12 python3.12-venv
  - On macOS: brew install python@3.12
EOF
  exit 1
fi

printf 'Python version: %s\n' "$PYTHON_VERSION"

# --- 1.6 / 1.4 Installation method ----------------------------------------
install_with_pipx() {
  printf '\nInstalling maily via pipx.\n'
  if ! command -v pipx >/dev/null 2>&1; then
    printf 'pipx was not found. Install pipx first, then re-run with --pipx:\n'
    cat <<'EOF'
  - macOS:      brew install pipx && pipx ensurepath
  - Ubuntu/Debian: sudo apt-get install pipx && pipx ensurepath
EOF
    exit 1
  fi
  run pipx install -e '.[gmail,secure,tui]'
  printf '\nSuccess! maily was installed via pipx.\n'
}

install_with_venv() {
  local venv_dir="${HOME}/.venv/maily"
  printf '\nSetting up a virtual environment at %s\n' "$venv_dir"

  # The venv layout differs on Windows (Scripts/) versus POSIX (bin/).
  local venv_python
  if [[ -d "$venv_dir/bin" ]]; then
    venv_python="$venv_dir/bin/python"
  elif [[ -d "$venv_dir/Scripts" ]]; then
    venv_python="$venv_dir/Scripts/python"
  else
    venv_python="$venv_dir/bin/python"
  fi

  if [[ ! -d "$venv_dir" ]]; then
    run "$PYTHON_BIN" -m venv "$venv_dir"
    printf 'Created virtual environment at %s\n' "$venv_dir"
  else
    printf 'Virtual environment already exists, reusing it.\n'
  fi

  run "$venv_python" -m pip install --upgrade pip

  if [[ "$DRY_RUN" -eq 0 ]]; then
    if ! "$venv_python" -m pip install -e '.[gmail,secure,tui]'; then
      printf '\npip install failed. You can try pipx as a fallback:\n' >&2
      printf '  ./install.sh --pipx\n' >&2
      exit 1
    fi
  else
    run "$venv_python" -m pip install -e '.[gmail,secure,tui]'
  fi

  if [[ "$DRY_RUN" -eq 0 ]] && [[ -x "$venv_python" ]]; then
    if "$venv_python" -c "import maily" >/dev/null 2>&1; then
      printf 'Verified: maily imports successfully from the virtual environment.\n'
    else
      printf 'Warning: could not import maily after install.\n' >&2
      exit 1
    fi
  fi

  printf '\nSuccess! maily was installed in the virtual environment at %s.\n' "$venv_dir"
  printf 'To activate it in future shells:\n'
  printf '  source %s/bin/activate\n' "$venv_dir"
}

if [[ "$USE_PIPX" -eq 1 ]]; then
  install_with_pipx
else
  install_with_venv
fi

printf '\nNext steps:\n'
printf '  1. maily init --oauth-client-file /path/to/client_secret.json\n'
printf '  2. maily scan\n'
if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '\n[dry-run] Done. No changes were made.\n'
fi