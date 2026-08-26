from datetime import datetime, timezone

from maily.classifier import Classifier
from maily.config import DEFAULT_CATEGORIES
from maily.models import EmailMessage


def test_deterministic_rule_does_not_need_provider():
    message = EmailMessage("1", "t", "", "alerts@example.com", "example.com", "Your verification code", "", datetime.now(timezone.utc), True, False)
    result, _ = Classifier(tuple(DEFAULT_CATEGORIES)).classify(message)
    assert result.categories == ["Action Required"]
    assert result.source == "deterministic"


def test_missing_provider_falls_back_to_other():
    message = EmailMessage("1", "t", "", "person@example.com", "example.com", "Hello", "", datetime.now(timezone.utc), True, False)
    result, _ = Classifier(tuple(DEFAULT_CATEGORIES)).classify(message)
    assert result.categories == ["Other"]
    assert result.degraded


def test_fake_provider_can_assign_multiple_categories():
    class FakeProvider:
        def classify(self, message, categories):
            return ["Work", "Action Required"]

    message = EmailMessage("1", "t", "", "person@example.com", "example.com", "Discussion", "", datetime.now(timezone.utc), True, False)
    result, _ = Classifier(tuple(DEFAULT_CATEGORIES), FakeProvider(), inference_enabled=True).classify(message)
    assert result.categories == ["Work", "Action Required"]
    assert result.source == "ollama"


def test_inference_disabled_falls_back_to_other():
    class FakeProvider:
        def classify(self, message, categories):
            return ["Work"]

    message = EmailMessage("1", "t", "", "person@example.com", "example.com", "Hello", "", datetime.now(timezone.utc), True, False)
    result, _ = Classifier(tuple(DEFAULT_CATEGORIES), FakeProvider(), inference_enabled=False).classify(message)
    assert result.categories == ["Other"]
    assert result.source == "fallback"
    assert not result.degraded


def test_inference_enabled_uses_provider():
    class FakeProvider:
        def classify(self, message, categories):
            return ["Work"]

    message = EmailMessage("1", "t", "", "person@example.com", "example.com", "Discussion", "", datetime.now(timezone.utc), True, False)
    result, _ = Classifier(tuple(DEFAULT_CATEGORIES), FakeProvider(), inference_enabled=True).classify(message)
    assert result.categories == ["Work"]
    assert result.source == "ollama"