## 1. Settings store

- [ ] 1.1 Add a small helper to read/write `~/.maily/settings.json` (theme key) and verify unit tests cover round-trip and missing-file default

## 2. Restore on mount

- [ ] 2.1 Apply the saved theme in `BrowseApp.on_mount` (or before mount) and verify a test asserts the app theme equals the saved value when a settings file exists, and the default when none exists

## 3. Persist on change

- [ ] 3.1 After a theme change, write the theme back to settings.json via a failure-tolerant helper and verify a test asserts the file is updated and that a write failure does not crash the TUI

## 4. Document default

- [ ] 4.1 Document the theme option in the default config template/settings docs and verify the template mentions the theme key

## 5. Full verification

- [ ] 5.1 Run the full gate: `ruff check`, `ruff format --check`, `mypy`, `pytest`, and `openspec validate --all` all pass