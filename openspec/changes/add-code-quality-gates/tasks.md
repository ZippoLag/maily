## 1. Tooling and environment

- [ ] 1.1 Add `ruff`, `mypy`, and `pytest-cov` to the dev dependencies in `pyproject.toml` and add `[tool.ruff]` (defaults, line-length 88), `[tool.mypy]` (files = maily, python_version = 3.11), and `[tool.coverage.run]` (branch, source = maily) sections
- [ ] 1.2 Establish the uv-managed project venv: ensure uv is available in the devcontainer (feature or postCreateCommand), run `uv sync` with dev extras, and verify tests run green from the `.venv` interpreter

## 2. One-time reformat

- [ ] 2.1 Run `ruff format` and `ruff check --fix` across `maily/` and `tests/` and commit the reformat *before* hooks are enabled
- [ ] 2.2 Verify `ruff check` and `ruff format --check` both exit clean with zero findings

## 3. Type-checking baseline

- [ ] 3.1 Run `mypy maily/` and fix all errors so a clean non-strict baseline is established

## 4. Coverage baseline and lift

- [ ] 4.1 Configure `pytest --cov=maily --cov-branch --cov-report=term-missing --cov-fail-under=65` and verify the current 64% baseline now passes the 65% floor once the planned new tests land
- [ ] 4.2 Add tests for the weakest modules to raise the floor: CLI human-readable output paths in `maily/cli.py` (target ≥ 60%), TUI helpers and modals in `maily/tui.py` (target ≥ 40%), and `maily/ollama.py` provider fallback paths (target ≥ 60%)

## 5. Pre-commit hook

- [ ] 5.1 Create `.githooks/pre-commit` (executable) running, in order: `ruff check`, `ruff format --check`, `mypy maily/`, `pytest --cov`; abort the commit on any failure
- [ ] 5.2 Wire `git config core.hooksPath .githooks` in the devcontainer setup and README; verify a failing gate blocks a commit and a clean tree commits normally

## 6. Documentation and verification

- [ ] 6.1 Update README with the developer setup (venv creation via uv, hook install, and a description of each gate)
- [ ] 6.2 Final verification: fresh `uv sync` install, all gates green from the venv, full test suite green, and `openspec validate --all` passes
