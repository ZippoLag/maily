# maily

> Author note: Project "maily" is my attempt at reaching inbox 0 and independence from the constant inflow of (somewhat relevant) emails I get across my email acounts, simplifying extraction of summary, action items, and actually human-to-human emails which need my focus, as well as other "urgencies" that may need my attention.

## Status

maily is currently a v1 foundation. It supports one Gmail account, local SQLite state, deterministic classification, user-configurable classification rules, optional local Ollama classification, offline rule learning from category corrections, CLI JSON output, and a TUI with email summaries and category editing. Scans can cover any historical date range with real-time progress reporting, date-chunked processing, and resumable sync state. Gmail mutations, scheduling, and multiple accounts are not implemented yet.

## Setup

Requires Python 3.11 or newer.

### Installation Options

The fastest way to install maily is the single-script installer, which
auto-detects your OS, checks for a compatible Python, and installs with all
extras into a virtual environment at `~/.venv/maily`:

```sh
./install.sh
```

To install via pipx instead of a virtual environment:

```sh
./install.sh --pipx
```

Run `./install.sh --help` for all available options.

### Advanced: Manual Installation

Prefer to install by hand? The installer relies on the same steps shown here.
The safest approach is a dedicated virtual environment:

```sh
python3 -m venv ~/.venv/maily
source ~/.venv/maily/bin/activate
pip install -e '.[gmail,secure,tui]'
```

To install maily for the current user with pipx instead:

```sh
brew install pipx   # on macOS
pipx install -e '.[gmail,secure,tui]'
```

A system-wide install (not recommended on macOS with Homebrew Python):

```sh
python3 -m pip install --break-system-packages -e '.[gmail,secure,tui]'
```

Note: On macOS with Homebrew-installed Python, you may see an "externally-managed-environment" error. Use one of the methods above to avoid this. See [PEP 668](https://peps.python.org/pep-0668/) for details.

Create a Google Cloud project, enable the Gmail API, configure an OAuth consent screen, create an OAuth client of type **Desktop app**, and download its JSON file. Initialize local state and provide the path:

```sh
maily init --oauth-client-file /path/to/client_secret.json
```

On the first scan, a browser window opens for Google authorization. maily requests read-only Gmail access and stores the resulting token in the operating system credential store. Tokens are not written to `~/.maily/config.toml`, SQLite, or logs.

## Scan

Run the today-focused scan manually:

```sh
maily scan
maily scan --json-format
```

The scan retrieves unread Gmail messages received today in the configured local timezone. Older unread and read counts are reported as deferred until a historical scan has run. If Ollama is available, unmatched messages are classified with the configured model; otherwise deterministic rules run and unresolved messages are assigned to `Other`.

### Historical scans

Any date range can be scanned, either as explicit dates or as a relative window:

```sh
maily scan --last 7days
maily scan --start-date 2024-01-01 --end-date 2024-01-31
maily scan --include-read --chunk-size week --verbose
maily scan --debug
```

- `--start-date` / `--end-date` — explicit `YYYY-MM-DD` bounds; each defaults to today when omitted
- `--last Ndays|Nweeks|Nmonths|Nyears` — relative window ending now
- `--include-read` — include already-read emails (defaults to the `[scan]` config)
- `--chunk-size day|week|month|year` — date chunk granularity for progress (default `day`)
- `--verbose` — add processing rate and ETA to progress output
- `--debug` — add per-chunk debug lines to progress output
- `--json-format` — machine-readable output on stdout; progress is written to stderr and never pollutes the JSON

Long scans stream email batches into the database chunk by chunk and report progress (percentage, current date chunk, counts, and optionally rate/ETA). If a scan is interrupted, `maily scan` resumes from the last processed chunk boundary on the next run.

Inspect or reset sync state with:

```sh
maily status          # shows last sync date, status, and processed count
maily status --reset  # asks for confirmation, then clears sync state
```

The default configuration is written to `~/.maily/config.toml`. It includes the local Ollama endpoint, the `gemma4:e2b` model, a 20-second timeout, the required categories, the classification inference setting, and a commented `[scan]` section. Edit configuration values there; maily preserves existing configuration on later launches.

Persistent scan defaults can be set in `~/.maily/config.toml` under `[scan]`; CLI flags override them:

```toml
[scan]
date_range = "last 30 days"   # "last 7 days", "this month", "2024-01-01:2024-01-31"
include_read = false          # set true to include already-read emails
chunk_size = "day"            # day | week | month | year
long_running = false          # lock against concurrent scans, save progress on interrupt
batch_size = 100              # emails per classify/commit batch
checkpoint_emails = 100       # save progress after every N emails
max_retries = 5               # Gmail rate-limit retries

[performance]
# memory_limit_mb = 1024      # warn when RSS approaches this limit
# body_cache_size = 500       # LRU cache for lazily loaded bodies

[suggestions]
# confidence_threshold = 0.0  # only show batch suggestions at/above this confidence
```

Invalid date ranges and unknown chunk sizes are rejected with a clear error when the config loads, so existing configurations without a `[scan]` section keep working unchanged.

## Long-Running Scans

For large backlogs, scan any date range and keep going overnight:

```sh
maily scan --last 30days --include-read --long-running
maily scan --start-date 2024-01-01 --end-date 2024-06-30 --verbose
```

- `--last N(days|weeks|months|years)` and `--start-date`/`--end-date` select the window
- `--include-read` fetches already-read mail as well
- `--long-running` prevents concurrent scans with a lock file and saves progress on interrupt (Ctrl+C) so the next scan resumes where it stopped
- `--verbose`/`--debug` increase progress verbosity (rate, ETA, per-chunk detail)
- `--batch-size N` controls how many emails are classified and committed per batch

Progress prints to stderr during the scan and mirrors to JSON Lines at `~/.maily/logs/scan_progress.jsonl`; scan errors append to `~/.maily/logs/scan_errors.log`.

### Progress and resilience

- Progress is checkpointed every `checkpoint_emails` (default 100) into the `sync_state` table; `maily status` reports it and `maily status --reset` clears it
- A failed chunk does not abort the scan: the error is classified (network/quota/unknown), reported, and remaining chunks still process — the scan finishes `degraded` with a partial result
- Gmail rate limits (429 / `rateLimitExceeded`) are retried with jittered exponential backoff up to `max_retries`; quota exhaustion stops gracefully with a clear message

By default, local inference is disabled to minimize resource usage. To enable it, add the following to your `config.toml`:

```toml
[classification]
inference_enabled = true
```

To use local inference, install Ollama, pull the configured model, and leave its local server available:

```sh
ollama pull gemma4:e2b
```

## Classification Rules

Static analysis rules run **before** inference and assign emails to categories deterministically based on regex patterns matched case-insensitively against the subject, body, and sender email. Default rules cover Action Required, Job search, and Newsletters - technical.

Add your own rules in `~/.maily/config.toml` under `[classification]`:

```toml
[[classification.rules]]
category = "Work"
patterns = [
  "meeting invitation",
  "project update",
  "status report",
]
fields = ["subject", "body"]
```

- `category` — the category to assign when a pattern matches
- `patterns` — regex patterns matched case-insensitively; any match assigns the category
- `fields` — optional message fields to match against (defaults to `["subject", "body", "sender_email"]`)

User rules are combined with the default rules. When an email matches multiple rules, it is assigned to **all** matching categories; the first matched rule in definition order becomes the primary category. Rules are validated when the config loads, and invalid regex patterns produce a clear configuration error.

## TUI

After installing the `tui` extra, launch:

```sh
maily tui
```

### Email Expansion

Navigate to an email in the tree and press **Enter** to expand it. Expanded emails show:
- Sender information (name and email address)
- Email body content

Use **Enter** again to collapse the email.

### Email Summary

Select an email and press **S** (Shift+s) to generate a summary. Summaries are:
- Generated using local Ollama inference when enabled and available
- Fall back to a deterministic preview (first 200 characters) when inference is unavailable
- Cached in the database for reuse

Summaries are displayed in a modal window. Press **Escape** to close the modal.

### Multi-Select

Select multiple emails to act on them together:
- **Space** toggles the focused email in the selection set
- **Ctrl+A** selects every email visible in the current viewport
- **Ctrl+D** (or **Escape** with no modal open) clears the selection
- Selected emails show a `[X]` checkbox prefix; the status bar shows the running count
- Selection survives scrolling and re-sorting

### Category Editing

Select an email and press **c** to open the category editor:
- The modal lists every configured category with a checkbox
- **Space** toggles a category on or off (arrow keys to navigate)
- **s** saves the change and persists it in the local database
- **Escape** cancels without saving

When multiple emails are selected, **c** applies the same category change to all of them at once, and asks you to confirm with **y** before saving. Each email shows its primary category with secondary categories as badges. The full category list is always visible in the status bar for the selected email.

### Gmail Label Badges

User-created Gmail labels render as colored badges next to each email in the tree (system labels like INBOX and SPAM are hidden). Long label lists are truncated with a `+N more` indicator. Press **l** to filter the view by the focused email's label; press **l** again to clear the filter.

### Batch Action Suggestions

Select several emails and press **b** to get batch action suggestions. Suggestions are generated deterministically from the selection (shared senders, labels, and newsletter patterns) and, when local inference is enabled, augmented with an AI-identified pattern. Each suggestion carries a confidence score:
- **Categorize** suggestions apply locally when accepted (press the suggestion number)
- **Archive / mark-read / delete** suggestions are read-only for now — they note that applying them needs Gmail write access in a future mutation workflow

Suggestions for the same selection are cached and reused.

### Rule Learning

Press **p** to review rule suggestions. maily analyzes your category corrections and, when a keyword appears in at least 3 emails you assigned to the same category, suggests it as a new rule:
- **a** accepts the suggestion and appends it to `config.toml`
- **r** rejects it

Suggestions persist across sessions until you act on them. Rule learning is fully offline and needs no inference.

### Large Result Sets

With thousands of emails, the tree groups each category by date (Today, Yesterday, Last Week, then month), shows the total count in the tree header, and paints lazily so navigation stays responsive. Email bodies are loaded from the database only when you expand the email. A progress bar is shown while the view loads.

### View Digest

Press **d** to summarize the emails currently visible in the tree: a count, a breakdown by category, and common themes. When inference is enabled, the digest is generated by Ollama; otherwise it falls back to deterministic counting and pattern matching. Digests are cached per view and shown in a modal — press **Escape** to dismiss. Scroll or change the sort order to digest a different view.

### Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `q` | Quit |
| `s` | Change sort order |
| `S` | Summarize selected email |
| `c` | Edit categories for selected email(s) |
| `m` | Mark/unmark selected email for batch editing |
| `p` | Review pending rule suggestions |
| `d` | Digest the currently visible emails |
| `Space` | Select/unselect focused email |
| `Ctrl+A` | Select all visible emails |
| `Ctrl+D` | Deselect all |
| `l` | Filter by focused email's label |
| `b` | Batch action suggestions |
| `u` | Undo last batch categorization |
| `i` | View pending mutation intents |
| `Page Up` / `Page Down` | Scroll by one page |
| `Home` / `End` | Jump to the first / last email |
| `Enter` | Expand/collapse email |
| `Escape` | Close modal / clear selection |



## Local State and Reset

The application stores configuration, SQLite state, migrations, and logs under `~/.maily/` (or the directory supplied through `--home`). The SQLite schema is versioned and migrations run before use. To reset local state, remove that directory and delete the `maily` Gmail credential from the operating system credential manager, then run `maily init` again.

## Updating

To update maily to the latest version, navigate to the project directory and reinstall:

```sh
cd /path/to/maily
git pull
pip install -e '.[gmail,secure,tui]'  # or use pipx if installed that way
```

If using a virtual environment, make sure to activate it first:
```sh
source ~/.venv/maily/bin/activate
cd /path/to/maily
git pull
pip install -e '.[gmail,secure,tui]'
```

## Development

### Project virtual environment (uv)

The project uses [uv](https://docs.astral.sh/uv/) to manage a reproducible `.venv` in the repo root (the `uv.lock` is generated by `uv sync`).

```sh
uv sync --extra dev   # installs the package and all dev dependencies
```

All quality gates below run through this environment. The devcontainer wires this up automatically (`postCreateCommand`); outside it, install uv via the [official installer](https://docs.astral.sh/uv/getting-started/installation/).

### Pre-commit hook

Every commit is gated by `.githooks/pre-commit`. Enable it once per clone:

```sh
git config core.hooksPath .githooks
```

The hook runs four gates in order and aborts the commit if any fails:

1. `ruff check` — lint
2. `ruff format --check` — formatting (run `ruff format` to apply)
3. `mypy maily` — type checking
4. `pytest --cov-fail-under=65` — full test suite with a 65% coverage floor

The coverage threshold is deliberately low enough to pass today; raise it as tests improve. Targeted per-test runs (`pytest tests/test_x.py`) collect coverage but do not enforce the floor — only the full-suite gate does.
