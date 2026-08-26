# maily

> Author note: Project "maily" is my attempt at reaching inbox 0 and independence from the constant inflow of (somewhat relevant) emails I get across my email acounts, simplifying extraction of summary, action items, and actually human-to-human emails which need my focus, as well as other "urgencies" that may need my attention.

## Status

maily is currently a v1 foundation. It supports one Gmail account, local SQLite state, deterministic classification, optional local Ollama classification, CLI JSON output, and the initial read-only TUI. Gmail mutations, historical synchronization, scheduling, and multiple accounts are not implemented yet.

## Setup

Requires Python 3.11 or newer.

### Installation Options

#### Using a virtual environment (recommended)
```sh
python3 -m venv ~/.venv/maily
source ~/.venv/maily/bin/activate
pip install -e '.[gmail,secure,tui]'
```

#### Using pipx (for CLI-only installation)
```sh
brew install pipx
pipx install -e '.[gmail,secure,tui]'
```

#### System-wide install (not recommended on macOS with Homebrew Python)
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

## Read-only TUI

After installing the `tui` extra, launch:

```sh
maily tui
```

The current TUI is intentionally browse-only. It does not mark messages read, delete mail, mark spam, create filters, or perform any other Gmail mutation.

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
