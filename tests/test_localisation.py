"""Tests for localisation readiness check."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agent import AdCopyInput, LocalisationResult, check_localisation

AD_INPUT = AdCopyInput(
    headline="Finally, Sunscreen That Doesn't Feel Like Sunscreen",
    body="Ultra-light SPF 50 that disappears into skin in seconds.",
    cta="Shop Now — Free Shipping Over $40",
    platform="facebook",
    target_audience="Women 25-40",
    campaign_goal="conversion",
    product_category="D2C skincare",
)

MOCK_FR_RESULT = {
    "target_locale": "fr-FR",
    "readiness_score": 62,
    "risks": [
        {
            "element": "Doesn't Feel Like Sunscreen",
            "risk": "Idiomatic — literal translation loses the sensory framing",
            "severity": "moderate",
        },
        {
            "element": "Free Shipping Over $40",
            "risk": "Currency mismatch — French market uses EUR not USD",
            "severity": "critical",
        },
    ],
    "translation_difficulty": "moderate",
    "locale_specific_suggestions": [
        "Replace '$40' with '35€' for French market",
        "Reframe headline as 'La crème solaire qui s\\'oublie sur la peau'",
    ],
    "summary": "Moderate localisation effort needed. Currency and idiomatic headline are critical fixes.",
}

MOCK_DE_RESULT = {
    "target_locale": "de-DE",
    "readiness_score": 78,
    "risks": [
        {
            "element": "Shop Now",
            "risk": "German audiences prefer more formal CTAs",
            "severity": "low",
        }
    ],
    "translation_difficulty": "easy",
    "locale_specific_suggestions": ["Use 'Jetzt kaufen' instead of direct 'Shop Now'"],
    "summary": "Good readiness for German market. Minor CTA adjustment recommended.",
}


def _mock_client(response: dict):
    mock = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(response))]
    mock.messages.create.return_value = msg
    return mock


def test_localisation_result_type():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_FR_RESULT)):
        result = check_localisation(AD_INPUT, "fr-FR")
    assert isinstance(result, LocalisationResult)


def test_target_locale_preserved():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_FR_RESULT)):
        result = check_localisation(AD_INPUT, "fr-FR")
    assert result.target_locale == "fr-FR"


def test_readiness_score_in_range():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_FR_RESULT)):
        result = check_localisation(AD_INPUT, "fr-FR")
    assert 0 <= result.readiness_score <= 100


def test_risks_have_valid_severity():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_FR_RESULT)):
        result = check_localisation(AD_INPUT, "fr-FR")
    for risk in result.risks:
        assert risk.severity in {"critical", "moderate", "low"}


def test_translation_difficulty_valid():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_FR_RESULT)):
        result = check_localisation(AD_INPUT, "fr-FR")
    assert result.translation_difficulty in {"easy", "moderate", "hard"}


def test_locale_suggestions_non_empty_when_risks_exist():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_FR_RESULT)):
        result = check_localisation(AD_INPUT, "fr-FR")
    assert len(result.locale_specific_suggestions) >= 1


def test_different_locale_returns_different_result():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_DE_RESULT)):
        result_de = check_localisation(AD_INPUT, "de-DE")
    assert result_de.target_locale == "de-DE"
    assert result_de.readiness_score != MOCK_FR_RESULT["readiness_score"]


def test_high_readiness_score_has_few_critical_risks():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_DE_RESULT)):
        result = check_localisation(AD_INPUT, "de-DE")
    critical_risks = [r for r in result.risks if r.severity == "critical"]
    assert len(critical_risks) == 0
