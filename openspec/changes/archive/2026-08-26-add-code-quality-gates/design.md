## Context

See proposal.md — Why. Measured baseline: 96 tests green, coverage 64% overall (tui.py 19%, cli.py 37%, ollama.py 32%, gmail.py 67%; core modules ≥ 89%), ~83% of functions annotated, 145 lines ≥ 88 chars. Tests currently run from the devcontainer's system Python 3.14 with `pip install -e '.[dev]'`; `uv.lock` exists but uv is not installed in the container.

## Goals / Non-Goals

- **Goals**: Formatter + linter + type check + coverage gate on every commit; reproducible project venv; one-time reformat so the gates start clean.
- **Non-Goals**: No CI pipeline (no repo-hosted CI exists; local gating is the ask). No strict-mode mypy yet. No coverage threshold higher than the measured baseline can sustain. No user-facing behavior changes.

## Decisions

- **ruff for lint + format, defaults adopted** (line-length 88): one Rust-fast tool replaces black + flake8 + isort, and the user opted into default style. Alternative (black/flake8/isort) rejected: three tools, three configs, slower.
- **mypy at non-strict baseline**: the code is already ~83% annotated, so a default-config run should be achievable without a large annotation campaign; strict mode is a follow-up. Config: `[tool.mypy] files = ["maily"]`, `python_version = "3.11"` (matching `requires-python` floor, conservative vs. 3.14 runtime).
- **Coverage floor = 65%, ratcheting**: measured today at 64%; `--cov-fail-under=65` with `--cov-branch` and `--cov-report=term-missing` in `[tool.coverage.run]`. The threshold rises as tests land (this change includes tasks to lift tui.py/cli.py/ollama.py). Alternative — an aspirational 80% gate — rejected: it would block every commit immediately until large test work lands.
- **Pre-commit hook runs all four gates on every commit** (user's explicit choice, accepting ~1–2 min/commit in the per-task TDD loop): `ruff check`, `ruff format --check`, `mypy`, `pytest --cov`. Plain `.githooks/pre-commit` script wired via `git config core.hooksPath .githooks` (set in the devcontainer and documented in README), running the venv's binaries. Alternative — the pre-commit framework — rejected for now: adds a dev dependency and its own isolated environments, while this repo's gate already runs through the standardized venv; revisitable if contributors arrive.
- **uv-managed venv**: `uv.lock` already exists and the toolchain script already knows uv, so `uv sync` (with dev extras declared in `[dependency-groups]` or the dev extra) is the canonical setup; uv is added to the devcontainer (feature or postCreateCommand). Alternative — plain `python3 -m venv` + pip — rejected as a second toolchain when uv is already intended; kept as fallback if uv proves problematic in the container.
- **Sequencing: baselines before the hook**: the one-time `ruff format`/`ruff check --fix` commit and the mypy cleanup must land before the hook is installed, or the first commit blocks on its own pre-existing diff.

## Risks / Trade-offs

- [Hook slows every per-task TDD commit (~1–2 min)] → accepted by the user; hook prints a one-line summary per gate and supports `--no-verify` for emergencies.
- [mypy non-strict misses real errors] → acceptable baseline; strict-mode task tracks tightening.
- [Coverage floor is barely above current → new code with untested paths can trip it] → that is the point; report lists uncovered lines so the fix is cheap.
- [uv unavailable in the container initially] → devcontainer change + README carry the install; until then gates fall back to the system Python env.
- [Reformat commit churns history] → done once, before hook enforcement; `git blame` noise is the accepted cost of starting clean.

## Migration Plan

1. Add dev deps + tool config to `pyproject.toml`; establish uv-managed `.venv`.
2. One-time reformat commit (`ruff format`, `ruff check --fix`) — no hook yet.
3. Establish clean mypy and coverage baselines (fix errors, add CLI/TUI/ollama tests).
4. Add `.githooks/pre-commit`, wire `core.hooksPath`, verify failing-gate blocks and clean-tree passes.
5. Update README; final full-suite + `openspec validate` verification. Rollback: uninstall hook (`git config --unset core.hooksPath`) or lower coverage threshold.
