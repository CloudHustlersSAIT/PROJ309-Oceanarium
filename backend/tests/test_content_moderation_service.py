from unittest.mock import patch

import pytest

from app.services.content_moderation import analyze_text, assert_text_is_safe
from app.services.exceptions import ValidationError


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, *args, **kwargs):
        return _FakeResponse(self._payload)


def test_assert_text_is_safe_blocks_on_blocklist_match(monkeypatch):
    monkeypatch.setenv("CONTENT_SAFETY_ENABLED", "true")
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_ENDPOINT", "https://example.cognitiveservices.azure.com")
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_KEY", "dummy")

    payload = {
        "categoriesAnalysis": [],
        "blocklistsMatch": [{"blocklistName": "oceanarium-profanity", "blocklistItemId": "1"}],
    }

    with patch("app.services.content_moderation.httpx.Client", return_value=_FakeClient(payload)):
        with pytest.raises(ValidationError, match="inappropriate content"):
            assert_text_is_safe("shitfuck", "first_name")


def test_analyze_text_blocks_on_blocklist_match(monkeypatch):
    monkeypatch.setenv("CONTENT_SAFETY_ENABLED", "true")
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_ENDPOINT", "https://example.cognitiveservices.azure.com")
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_KEY", "dummy")
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_BLOCKLIST_NAMES", "oceanarium-profanity")

    payload = {
        "categoriesAnalysis": [],
        "blocklistsMatch": [{"blocklistName": "oceanarium-profanity", "blocklistItemId": "1"}],
    }

    with patch("app.services.content_moderation.httpx.Client", return_value=_FakeClient(payload)):
        result = analyze_text("any text")

    assert result["blocked"] is True
    assert len(result["blocklist_matches"]) == 1


def test_analyze_text_sends_blocklist_names(monkeypatch):
    monkeypatch.setenv("CONTENT_SAFETY_ENABLED", "true")
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_ENDPOINT", "https://example.cognitiveservices.azure.com")
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_KEY", "dummy")
    monkeypatch.setenv("AZURE_CONTENT_SAFETY_BLOCKLIST_NAMES", "oceanarium-profanity,secondary-list")

    captured: dict = {}

    class _CapturingClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, *args, **kwargs):
            captured["json"] = kwargs.get("json")
            return _FakeResponse({"categoriesAnalysis": [], "blocklistsMatch": []})

    with patch("app.services.content_moderation.httpx.Client", return_value=_CapturingClient()):
        analyze_text("any text")

    assert captured["json"]["blocklistNames"] == ["oceanarium-profanity", "secondary-list"]