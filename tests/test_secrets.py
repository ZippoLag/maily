import sys
import types

from maily.secrets import CredentialStore


def test_credential_store_delegates_to_keyring(monkeypatch):
    values = {}
    fake_keyring = types.SimpleNamespace(
        get_password=lambda service, key: values.get((service, key)),
        set_password=lambda service, key, value: values.__setitem__(
            (service, key), value
        ),
        delete_password=lambda service, key: values.pop((service, key), None),
    )
    monkeypatch.setitem(sys.modules, "keyring", fake_keyring)
    store = CredentialStore()
    store.set("gmail:oauth", "secret-token")
    assert store.get("gmail:oauth") == "secret-token"
    store.delete("gmail:oauth")
    assert store.get("gmail:oauth") is None
