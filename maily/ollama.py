from __future__ import annotations

import json
import urllib.error
import urllib.request

from .models import EmailMessage


class OllamaProvider:
    def __init__(self, url: str, model: str, timeout_seconds: float):
        self.url = url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def classify(self, message: EmailMessage, categories: tuple[str, ...]) -> list[str]:
        prompt = {
            "categories": categories,
            "message": {
                "sender": message.sender_email,
                "subject": message.subject,
                "body": message.body,
            },
            "instruction": "Return JSON only: {\"categories\": [category names]}. Choose zero or more categories.",
        }
        request = urllib.request.Request(
            f"{self.url}/api/generate",
            data=json.dumps({"model": self.model, "prompt": json.dumps(prompt), "stream": False, "format": "json"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama unavailable: {exc}") from exc
        output = json.loads(payload.get("response", "{}"))
        return output.get("categories", [])

    def generate(self, prompt: str) -> str:
        """Generate a text response from a prompt."""
        request = urllib.request.Request(
            f"{self.url}/api/generate",
            data=json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama unavailable: {exc}") from exc
        return payload.get("response", "")