from pathlib import Path

import pytest

from maily import auth
from maily.config import DEFAULT_CATEGORIES, load_config
from maily.db import Database


class FakeCredentials:
    def get(self, key):
        return None

    def set(self, key, value):
        pass


def test_authentication_rejects_a_second_account(monkeypatch, tmp_path: Path):
    config = load_config(tmp_path / ".maily")
    database = Database(config.database_file)
    database.seed_categories(tuple(DEFAULT_CATEGORIES))
    with database.transaction() as connection:
        connection.execute(
            "INSERT INTO accounts(email, credential_key, created_at) VALUES ('old@example.com', 'gmail:oauth', 'now')"
        )
    monkeypatch.setattr(
        auth,
        "build_authenticated_client",
        lambda *args: (object(), "new@example.com", "token"),
    )
    with pytest.raises(RuntimeError, match="exactly one"):
        auth.authenticate(tmp_path / "client.json", database, FakeCredentials())
    database.close()
