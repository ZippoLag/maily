# maily

> Author note: Project "maily" is my attempt at reaching inbox 0 and independence from the constant inflow of (somewhat relevant) emails I get across my email acounts, simplifying extraction of summary, action items, and actually human-to-human emails which need my focus, as well as other "urgencies" that may need my attention.

## Status

maily is currently a v1 foundation. It supports one Gmail account, local SQLite state, deterministic classification, user-configurable classification rules, optional local Ollama classification, offline rule learning from category corrections, CLI JSON output, and a TUI with email summaries and category editing. Gmail mutations, historical synchronization, scheduling, and multiple accounts are not implemented yet.

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

## Daily Scan

Run the initial today-focused scan manually:

```sh
maily scan
maily scan --json-format
```

The scan retrieves unread Gmail messages received today in the configured local timezone. Older unread and read counts are reported as deferred until historical synchronization is added. If Ollama is available, unmatched messages are classified with the configured model; otherwise deterministic rules run and unresolved messages are assigned to `Other`.

The default configuration is written to `~/.maily/config.toml`. It includes the local Ollama endpoint, the `gemma4:e2b` model, a 20-second timeout, the required categories, and the classification inference setting. Edit configuration values there; maily preserves existing configuration on later launches.

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

### Category Editing

Select an email and press **c** to open the category editor:
- The modal lists every configured category with a checkbox
- **Space** toggles a category on or off (arrow keys to navigate)
- **s** saves the change and persists it in the local database
- **Escape** cancels without saving

Mark multiple emails with **m** before pressing **c** to apply the same category change to all marked emails at once.

Each email shows its primary category with secondary categories as badges. The full category list is always visible in the status bar for the selected email.

### Rule Learning

Press **p** to review rule suggestions. maily analyzes your category corrections and, when a keyword appears in at least 3 emails you assigned to the same category, suggests it as a new rule:
- **a** accepts the suggestion and appends it to `config.toml`
- **r** rejects it

Suggestions persist across sessions until you act on them. Rule learning is fully offline and needs no inference.

### Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `q` | Quit |
| `s` | Change sort order |
| `S` | Summarize selected email |
| `c` | Edit categories for selected email(s) |
| `m` | Mark/unmark selected email for batch editing |
| `p` | Review pending rule suggestions |
| `Enter` | Expand/collapse email |
| `Escape` | Close modal |



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
