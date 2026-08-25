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
    result, _ = Classifier(tuple(DEFAULT_CATEGORIES), FakeProvider()).classify(message)
    assert result.categories == ["Work", "Action Required"]
    assert result.source == "ollama"