from __future__ import annotations

import hashlib
import json
import re
from typing import Protocol

from .config import DEFAULT_RULES, Rule
from .models import ClassificationResult, EmailMessage


class InferenceProvider(Protocol):
    def classify(self, message: EmailMessage, categories: tuple[str, ...]) -> list[str]: ...


def fingerprint(message: EmailMessage, categories: tuple[str, ...], rules: tuple[Rule, ...]) -> str:
    payload = {
        "message": message.as_dict(),
        "categories": categories,
        "rules": [rule.__dict__ for rule in rules],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class Classifier:
    def __init__(self, categories: tuple[str, ...], provider: InferenceProvider | None = None, rules: tuple[Rule, ...] | None = None, inference_enabled: bool = False):
        self.categories = categories
        self.provider = provider
        self.rules = rules if rules is not None else DEFAULT_RULES
        self.inference_enabled = inference_enabled

    def classify(self, message: EmailMessage) -> tuple[ClassificationResult, str]:
        matched = list(dict.fromkeys(rule.category for rule in self.rules if rule.matches(message)))
        if matched:
            return ClassificationResult(matched, "deterministic"), fingerprint(message, self.categories, self.rules)
        if self.provider is None or not self.inference_enabled:
            return ClassificationResult(["Other"], "fallback", degraded=True if self.provider is None else False, error="Inference provider unavailable" if self.provider is None else None), fingerprint(message, self.categories, self.rules)
        try:
            inferred = [category for category in self.provider.classify(message, self.categories) if category in self.categories]
            return ClassificationResult(list(dict.fromkeys(inferred or ["Other"])), "ollama"), fingerprint(message, self.categories, self.rules)
        except Exception as exc:
            return ClassificationResult(["Other"], "fallback", degraded=True, error=str(exc)), fingerprint(message, self.categories, self.rules)