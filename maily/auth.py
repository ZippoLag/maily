from __future__ import annotations

from pathlib import Path

from .db import Database, iso_now
from .gmail import build_authenticated_client
from .secrets import CredentialStore


def authenticate(client_file: Path, database: Database, credentials: CredentialStore):
    token_key = "gmail:oauth"
    client, email, token_json = build_authenticated_client(
        client_file, credentials.get(token_key)
    )
    credentials.set(token_key, token_json)
    with database.transaction() as connection:
        existing = connection.execute("SELECT email FROM accounts").fetchone()
        if existing and existing[0] != email:
            raise RuntimeError(
                "v1 supports exactly one Gmail account; remove the existing account before authenticating another"
            )
        connection.execute(
            "INSERT INTO accounts(email, credential_key, created_at) VALUES (?, ?, ?) ON CONFLICT(email) DO UPDATE SET credential_key=excluded.credential_key",
            (email, token_key, iso_now()),
        )
    return client, email
