import json
import urllib.error
from types import SimpleNamespace

import pytest

from maily.ollama import OllamaProvider


class FakeResponse:
    def __init__(self, data: bytes):
        self._data = data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._data


def provider():
    return OllamaProvider("http://127.0.0.1:11434", "test-model", 5.0)


def message():
    return SimpleNamespace(
        sender_email="alice@example.com", subject="Hello", body="Body"
    )


def test_classify_returns_categories(monkeypatch):
    body = json.dumps(
        {"response": json.dumps({"categories": ["Work", "Personal"]})}
    ).encode()
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda request, timeout: FakeResponse(body)
    )
    result = provider().classify(message(), ("Work", "Personal"))
    assert result == ["Work", "Personal"]


def test_classify_raises_on_url_error(monkeypatch):
    def boom(request, timeout):
        raise urllib.error.URLError("down")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(RuntimeError, match="Ollama unavailable"):
        provider().classify(message(), ("Work",))


def test_classify_raises_on_bad_json(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda request, timeout: FakeResponse(b"not json")
    )
    with pytest.raises(RuntimeError, match="Ollama unavailable"):
        provider().classify(message(), ("Work",))


def test_generate_returns_text(monkeypatch):
    body = json.dumps({"response": "A summary"}).encode()
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda request, timeout: FakeResponse(body)
    )
    assert provider().generate("Summarize") == "A summary"


def test_generate_raises_on_timeout(monkeypatch):
    def boom(request, timeout):
        raise TimeoutError("timed out")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(RuntimeError, match="Ollama unavailable"):
        provider().generate("Summarize")
