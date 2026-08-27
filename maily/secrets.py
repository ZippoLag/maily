from __future__ import annotations


class CredentialStoreError(RuntimeError):
    pass


class CredentialStore:
    def __init__(self, service: str = "maily"):
        self.service = service
        try:
            import keyring
        except ImportError as exc:
            raise CredentialStoreError(
                "Install maily with the 'secure' extra to enable OS credential storage"
            ) from exc
        self._keyring = keyring

    def get(self, key: str) -> str | None:
        return self._keyring.get_password(self.service, key)

    def set(self, key: str, value: str) -> None:
        self._keyring.set_password(self.service, key, value)

    def delete(self, key: str) -> None:
        self._keyring.delete_password(self.service, key)
