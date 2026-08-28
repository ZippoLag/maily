## Why

The digest and summarize views have confusing scope and formatting: the digest only covers the currently selected/visible emails, the "Summarize" view duplicates digest behavior, and category totals are poorly formatted. This makes daily review incomplete and hard to scan.

## What Changes

- **Digest (`D`)** always summarizes **all emails in all categories for the current date** — regardless of whether they are marked or selected. Hotkey changes from `d` to **`D`**. It generates **one paragraph per non-empty category**.
- **Summarize (`S`)** summarizes all **marked** emails individually, a brief paragraph each. If no email is marked, it uses only the **selected** (highlighted) email. If neither exists, the view does **not** open and a message explains why.
- **Totals by category** in digest and summarize views are formatted as a readable list (not raw inline).

## Capabilities

### New Capabilities
_None._

### Modified Capabilities
- `tui/email-summary`: The `S` summarize scope changes to marked-messages → selected fallback → no-open message; per-email paragraphs.
- `email-presentation/digest-current-view`: The digest scope becomes all current-date emails in all categories (regardless of mark/selection), one paragraph per non-empty category; hotkey changes from `d` to `D`; formatted totals list.

## Impact

- `maily/tui.py` — `action_summarize`, `action_digest_current`, group-scope logic, totals formatting.
- `README.md` — shortcut table (`S`, `D`).
- Specs `tui/email-summary` and `email-presentation/digest-current-view` modified; `tui/digest` may be created.