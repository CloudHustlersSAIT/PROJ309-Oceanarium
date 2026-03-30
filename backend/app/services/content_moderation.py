from __future__ import annotations

import os
from typing import Any

import httpx

from .exceptions import ValidationError


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _is_enabled() -> bool:
    return _as_bool(os.getenv("CONTENT_SAFETY_ENABLED"), default=False)


def _is_fail_closed() -> bool:
    return _as_bool(os.getenv("CONTENT_SAFETY_FAIL_CLOSED"), default=False)


def _build_url(endpoint: str) -> str:
    api_version = os.getenv("AZURE_CONTENT_SAFETY_API_VERSION", "2024-09-01")
    return f"{endpoint.rstrip('/')}/contentsafety/text:analyze?api-version={api_version}"


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_csv_env(name: str) -> list[str]:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _get_blocklist_names() -> list[str]:
    return _get_csv_env("AZURE_CONTENT_SAFETY_BLOCKLIST_NAMES")


def _parse_categories(payload: dict) -> list[dict]:
    categories = payload.get("categoriesAnalysis")
    if isinstance(categories, list):
        return categories
    return []


def _parse_blocklist_matches(payload: dict[str, Any]) -> list[dict[str, Any]]:
    matches = payload.get("blocklistsMatch")
    if isinstance(matches, list):
        return [match for match in matches if isinstance(match, dict)]
    return []


def analyze_text(text: str) -> dict:
    """Analyze text with Azure Content Safety.

    Returns a dict with keys:
    - enabled: bool
    - blocked: bool
    - matched_categories: list[dict]
    """
    if not _is_enabled():
        return {"enabled": False, "blocked": False, "matched_categories": []}

    endpoint = (os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT") or "").strip()
    key = (os.getenv("AZURE_CONTENT_SAFETY_KEY") or "").strip()
    threshold = _get_int_env("CONTENT_SAFETY_BLOCK_SEVERITY", default=2)
    blocklist_names = _get_blocklist_names()

    if not endpoint or not key:
        if _is_fail_closed():
            raise ValidationError("Content moderation is enabled but Azure Content Safety is not configured")
        return {"enabled": True, "blocked": False, "matched_categories": []}

    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "api-key": key,
        "Content-Type": "application/json",
    }

    request_body: dict[str, Any] = {"text": text}
    if blocklist_names:
        request_body["blocklistNames"] = blocklist_names

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(_build_url(endpoint), headers=headers, json=request_body)
            response.raise_for_status()
            data = response.json()
    except Exception:
        if _is_fail_closed():
            raise ValidationError("Unable to validate content safety at this time")
        return {"enabled": True, "blocked": False, "matched_categories": []}

    matched_categories: list[dict] = []
    for category in _parse_categories(data):
        severity = int(category.get("severity", 0))
        if severity >= threshold:
            matched_categories.append(
                {
                    "category": category.get("category", "unknown"),
                    "severity": severity,
                }
            )

    blocklist_matches = _parse_blocklist_matches(data)

    return {
        "enabled": True,
        "blocked": len(matched_categories) > 0 or len(blocklist_matches) > 0,
        "matched_categories": matched_categories,
        "blocklist_matches": blocklist_matches,
    }


def assert_text_is_safe(text: str | None, field_name: str) -> None:
    cleaned = (text or "").strip()
    if not cleaned:
        return

    result = analyze_text(cleaned)
    if not result["blocked"]:
        return

    raise ValidationError(f"{field_name} contains inappropriate content and cannot be saved")
