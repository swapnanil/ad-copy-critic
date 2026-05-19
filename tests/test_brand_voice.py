"""Tests for brand voice compliance — rule-based checks need no LLM mock."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agent import AdCopyInput, BrandVoiceProfile, BrandVoiceResult, check_brand_voice
from agent.models import VoiceViolation

STRICT_PROFILE = BrandVoiceProfile(
    brand_name="VitaGlow",
    prohibited_words=["revolutionary", "world-class", "best-in-class", "proven"],
    required_tone="warm, direct, customer-first — never hype, never superlatives",
    persona="A knowledgeable friend, not a salesperson",
    example_good_copy=["Skin that feels like yours again.", "SPF that disappears."],
    example_bad_copy=["The world's best skincare.", "Revolutionise your routine."],
)

COMPLIANT_AD = AdCopyInput(
    headline="Sunscreen That Disappears Into Your Skin",
    body="Ultra-light SPF 50. Reef-safe. Ready in 30 seconds.",
    cta="Try It Today",
    platform="facebook",
    target_audience="Women 25-40",
    campaign_goal="conversion",
    product_category="D2C skincare",
)

VIOLATING_AD = AdCopyInput(
    headline="The Revolutionary Skincare That's World-Class",
    body="Proven formula, best-in-class results.",
    cta="Shop Now",
    platform="facebook",
    target_audience="Women 25-40",
    campaign_goal="conversion",
    product_category="D2C skincare",
)

CLEAN_LLM_RESPONSE = {
    "compliant": True,
    "compliance_score": 88,
    "violations": [],
    "suggestions": [],
    "voice_summary": "Ad copy aligns well with the warm, direct tone required.",
}

TONE_VIOLATION_RESPONSE = {
    "compliant": False,
    "compliance_score": 40,
    "violations": [
        {
            "field": "body",
            "text": "Proven formula, best-in-class results.",
            "rule": "Hype language contradicts warm, customer-first persona",
            "severity": "moderate",
        }
    ],
    "suggestions": ["Lead with the customer benefit, not the product claim."],
    "voice_summary": "Copy leans into hype and superlatives, contradicting the brand persona.",
}


def _mock_client(response: dict):
    mock = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(response))]
    mock.messages.create.return_value = msg
    return mock


def test_prohibited_word_in_headline_flagged_without_llm():
    with patch("agent.critic._get_client", return_value=_mock_client(CLEAN_LLM_RESPONSE)):
        result = check_brand_voice(VIOLATING_AD, STRICT_PROFILE)
    prohibited_violations = [v for v in result.violations if "Prohibited word" in v.rule]
    assert len(prohibited_violations) >= 2  # "revolutionary" and "world-class"


def test_prohibited_word_sets_not_compliant():
    with patch("agent.critic._get_client", return_value=_mock_client(CLEAN_LLM_RESPONSE)):
        result = check_brand_voice(VIOLATING_AD, STRICT_PROFILE)
    assert result.compliant is False


def test_prohibited_word_caps_compliance_score():
    with patch("agent.critic._get_client", return_value=_mock_client({"compliant": True, "compliance_score": 90, "violations": [], "suggestions": [], "voice_summary": "Fine."})):
        result = check_brand_voice(VIOLATING_AD, STRICT_PROFILE)
    assert result.compliance_score <= 50


def test_compliant_ad_no_prohibited_words():
    with patch("agent.critic._get_client", return_value=_mock_client(CLEAN_LLM_RESPONSE)):
        result = check_brand_voice(COMPLIANT_AD, STRICT_PROFILE)
    prohibited_violations = [v for v in result.violations if "Prohibited word" in v.rule]
    assert len(prohibited_violations) == 0


def test_llm_tone_violations_merged():
    with patch("agent.critic._get_client", return_value=_mock_client(TONE_VIOLATION_RESPONSE)):
        result = check_brand_voice(VIOLATING_AD, STRICT_PROFILE)
    tone_violations = [v for v in result.violations if "Prohibited word" not in v.rule]
    assert len(tone_violations) >= 1


def test_result_is_brand_voice_result_type():
    with patch("agent.critic._get_client", return_value=_mock_client(CLEAN_LLM_RESPONSE)):
        result = check_brand_voice(COMPLIANT_AD, STRICT_PROFILE)
    assert isinstance(result, BrandVoiceResult)
    assert isinstance(result.compliance_score, int)
    assert 0 <= result.compliance_score <= 100


def test_no_prohibited_words_profile_passes_rule_check():
    lenient = BrandVoiceProfile(
        brand_name="GenericBrand",
        prohibited_words=[],
        required_tone="friendly",
    )
    with patch("agent.critic._get_client", return_value=_mock_client(CLEAN_LLM_RESPONSE)):
        result = check_brand_voice(VIOLATING_AD, lenient)
    prohibited_violations = [v for v in result.violations if "Prohibited word" in v.rule]
    assert len(prohibited_violations) == 0


def test_violation_field_correctly_identified():
    ad_with_cta_violation = AdCopyInput(
        headline="Great Skincare",
        cta="The Revolutionary Solution",
        platform="facebook",
        target_audience="Women",
        campaign_goal="conversion",
        product_category="skincare",
    )
    with patch("agent.critic._get_client", return_value=_mock_client(CLEAN_LLM_RESPONSE)):
        result = check_brand_voice(ad_with_cta_violation, STRICT_PROFILE)
    cta_violations = [v for v in result.violations if v.field == "cta"]
    assert len(cta_violations) >= 1
