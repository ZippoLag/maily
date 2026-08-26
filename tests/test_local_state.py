from pathlib import Path

from maily.config import DEFAULT_CATEGORIES, load_config
from maily.db import Database


def test_first_launch_creates_restricted_state(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    assert config.database_file.parent.exists()
    assert (config.home / "config.toml").exists()
    assert set(DEFAULT_CATEGORIES).issubset(config.categories)


def test_database_migrates_and_seeds_categories(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    assert database.connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 8
    assert database.connection.execute("SELECT version FROM schema_version").fetchone()[0] == 2
    database.close()


def test_database_creates_user_category_overrides_table(tmp_path: Path):
    database = Database(tmp_path / "maily.sqlite3")
    table = database.connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'user_category_overrides'"
    ).fetchone()
    assert table is not None
    database.close()


def test_config_parses_inference_enabled_default(tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    assert config.inference_enabled == False


def test_config_parses_inference_enabled_true(tmp_path: Path):
    config_dir = tmp_path / ".maily"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text("""timezone = "UTC"
[classification]
inference_enabled = true
[gmail]
oauth_client_file = ""
""")
    config = load_config(config_dir)
    assert config.inference_enabled == True