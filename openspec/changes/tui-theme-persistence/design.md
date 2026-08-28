# Design: TUI Theme Persistence

## Context

See proposal.md — Why. The TUI is a Textual app with built-in theme switching (e.g. `Ctrl+T`), but `App.theme` resets to the default each launch.

## Goals / Non-Goals

- **Goals**: Persist the selected theme and restore it on startup.
- **Non-Goals**: No new theme catalog or custom themes. No theme-cycling UI changes beyond persistence.

## Decisions

- **Persist in a small runtime settings file** at `~/.maily/settings.json` (`{"theme": "<name>"}`), separate from `config.toml`. Rationale: `config.toml` is a user-edited launch-time TOML with a protected default writer; the theme is a runtime choice best stored as lightweight JSON. `MailyConfig.home` provides the directory.
- **Load on mount**: in `BrowseApp.on_mount`, read `settings.json`; if present set `self.theme = X` before/at mount (Textual lets `App.theme` be assigned programmatically). If absent, keep the default.
- **Persist on change**: wrap/observe the theme switcher action; after a theme change, write `{"theme": self.theme}` back to `settings.json`. Use a `_persist_theme()` helper guarded against I/O errors (never crash the TUI if the write fails).
- **Document in defaults**: add a `theme = "textual-dark"` (or similar default) option to the default config template's settings documentation; the runtime settings file is where the active value lives.

## Risks / Trade-offs

- Runtime JSON settings could get out of sync with `config.toml` -> mitigated by keeping theme exclusively in `settings.json` and documenting that.
- `App.theme` assignment timing in Textual -> mitigated by testing on_mount application; if direct assignment is unreliable, use `App.set_theme()`.

## Migration Plan

None (new optional file; absence is handled by the default).

## Open Questions

Which exact default theme name should be documented depends on Textual's built-in names (`textual-dark` etc.); resolve at implementation time without changing specs.