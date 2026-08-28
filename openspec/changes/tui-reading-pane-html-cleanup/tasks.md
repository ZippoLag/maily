## 1. Dependency

- [ ] 1.1 Add `html2text` to `pyproject.toml` dependencies and verify `pip install -e .` resolves it (import succeeds)

## 2. Conversion helper

- [ ] 2.1 Add an `html_to_readable(body)` helper that converts HTML to Markdown, passes plain text through, and falls back to the original body on error, and verify unit tests cover HTML, plain-text, and failure cases
- [ ] 2.2 Wire the helper into `email_pane_text` so HTML bodies render converted text and verify the render test passes for an HTML body

## 3. Full verification

- [ ] 3.1 Run the full gate: `ruff check`, `ruff format --check`, `mypy`, `pytest`, and `openspec validate --all` all pass