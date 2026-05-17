"""Tests for the core critique logic."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agent import AdCopyInput, AdCritique, critique_ad
from agent.critic import critique_batch

MOCK_CRITIQUE_VALID = {
    "overall_score": 72,
    "overall_verdict": "strong",
    "executive_summary": "This ad demonstrates strong clarity and platform fit. The CTA is direct and benefit-led.",
    "dimensions": [
        {"dimension": "Clarity", "score": 8, "verdict": "Clear and specific.", "issue": None, "fix": None},
        {"dimension": "Audience Fit", "score": 7, "verdict": "Well targeted.", "issue": None, "fix": None},
        {"dimension": "CTA Strength", "score": 7, "verdict": "Action-oriented CTA.", "issue": None, "fix": None},
        {"dimension": "Value Proposition", "score": 8, "verdict": "Differentiators are explicit.", "issue": None, "fix": None},
        {"dimension": "Emotional Hook", "score": 7, "verdict": "Hooks on frustration relief.", "issue": None, "fix": None},
        {"dimension": "Platform Fit", "score": 7, "verdict": "Appropriate for platform.", "issue": None, "fix": None},
        {"dimension": "Credibility", "score": 6, "verdict": "Claims need more proof.", "issue": "Unverified superlative.", "fix": "Add a statistic."},
        {"dimension": "Brevity", "score": 6, "verdict": "Slightly verbose.", "issue": None, "fix": None},
    ],
    "critical_issues": [],
    "minor_issues": ["Body copy slightly long for mobile."],
    "strengths": ["Strong emotional hook.", "Clear value proposition."],
    "variants": [
        {
            "label": "Variant A",
            "headline": "Improved Headline A",
            "body": "Improved body copy.",
            "cta": "Get Started Free",
            "rationale": "Tighter and more benefit-led.",
        },
        {
            "label": "Variant B",
            "headline": "Improved Headline B",
            "body": "Alternative body copy.",
            "cta": "Try It Now",
            "rationale": "Tests social proof framing.",
        },
    ],
    "ab_test_recommendation": "Run Variant A vs control for 7 days.",
    "platform_fit_note": "Good platform fit for this format.",
}

MOCK_CRITIQUE_WEAK = {
    **MOCK_CRITIQUE_VALID,
    "overall_score": 20,
    "overall_verdict": "do_not_run",
    "executive_summary": "This ad has critical issues that will harm brand performance.",
}

FINTECH_INPUT = AdCopyInput(
    headline="Grow Your Business with Our Financial Solutions",
    body="We offer a wide range of financial products.",
    cta="Learn More",
    platform="linkedin",
    target_audience="CFOs and finance directors",
    campaign_goal="lead_generation",
    product_category="B2B fintech",
    usp="Approval in 24 hours",
)

ECOMMERCE_INPUT = AdCopyInput(
    headline="Finally, Sunscreen That Doesn't Feel Like Sunscreen",
    body="Ultra-light SPF 50 that disappears into skin in seconds.",
    cta="Shop Now — Free Shipping Over $40",
    platform="facebook",
    target_audience="Women 25-40 interested in skincare",
    campaign_goal="conversion",
    product_category="D2C skincare",
    usp="Invisible finish, SPF 50, reef-safe",
)

SAAS_INPUT = AdCopyInput(
    headline="Project Management Software",
    body="Manage your projects better with our software.",
    cta="Get Started",
    platform="google_search",
    target_audience="Operations managers at SMBs",
    campaign_goal="conversion",
    product_category="SaaS project management",
    usp="AI-powered task prioritisation",
    character_limits={"headline": 30, "body": 90},
)


def _make_mock_api(response_json: dict):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(response_json))]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@patch("agent.critic._get_client")
def test_critique_score_range(mock_get_client):
    mock_get_client.return_value = _make_mock_api(MOCK_CRITIQUE_VALID)
    result = critique_ad(ECOMMERCE_INPUT)
    assert isinstance(result, AdCritique)
    assert 1 <= result.overall_score <= 100


@patch("agent.critic._get_client")
def test_critique_variants_count(mock_get_client):
    mock_get_client.return_value = _make_mock_api(MOCK_CRITIQUE_VALID)
    result = critique_ad(ECOMMERCE_INPUT)
    assert 2 <= len(result.variants) <= 3


@patch("agent.critic._get_client")
def test_do_not_run_only_when_score_below_25(mock_get_client):
    mock_get_client.return_value = _make_mock_api(MOCK_CRITIQUE_WEAK)
    result = critique_ad(FINTECH_INPUT)
    assert result.overall_score < 25
    assert result.overall_verdict == "do_not_run"


@patch("agent.critic._get_client")
def test_strong_verdict_not_do_not_run(mock_get_client):
    mock_get_client.return_value = _make_mock_api(MOCK_CRITIQUE_VALID)
    result = critique_ad(ECOMMERCE_INPUT)
    assert result.overall_score >= 25
    assert result.overall_verdict != "do_not_run"


@patch("agent.critic._get_client")
def test_character_limit_violation_flagged(mock_get_client):
    """Headline 'Project Management Software' is 28 chars; limit is 30 so no violation.
    Body 'Manage your projects better with our software.' is 46 chars; limit 90 so no violation.
    Test a real violation by patching the input."""
    response = {**MOCK_CRITIQUE_VALID, "critical_issues": []}
    mock_get_client.return_value = _make_mock_api(response)

    # Create input where headline exceeds its limit
    ad = AdCopyInput(
        headline="This Headline Is Way Too Long For The Limit",
        body="Short body.",
        cta="Buy Now",
        platform="google_search",
        target_audience="General audience",
        campaign_goal="conversion",
        product_category="Software",
        character_limits={"headline": 10},
    )
    result = critique_ad(ad)
    assert any("headline" in issue.lower() for issue in result.critical_issues)


@patch("agent.critic._get_client")
def test_empty_headline_raises(mock_get_client):
    mock_get_client.return_value = _make_mock_api(MOCK_CRITIQUE_VALID)
    with pytest.raises(ValueError, match="Headline cannot be empty"):
        critique_ad(
            AdCopyInput(
                headline="   ",
                platform="facebook",
                target_audience="Anyone",
                campaign_goal="awareness",
                product_category="Generic",
            )
        )


@patch("agent.critic._get_client")
def test_batch_returns_fleet_summary(mock_get_client):
    mock_get_client.return_value = _make_mock_api(MOCK_CRITIQUE_VALID)
    result = critique_batch([FINTECH_INPUT, ECOMMERCE_INPUT])
    assert result.fleet_summary
    assert len(result.critiques) == 2
    assert 1 <= result.average_score <= 100
    assert result.weakest_dimension


@patch("agent.critic._get_client")
def test_saas_google_search_critiqued(mock_get_client):
    mock_get_client.return_value = _make_mock_api(MOCK_CRITIQUE_VALID)
    result = critique_ad(SAAS_INPUT)
    assert isinstance(result, AdCritique)
    assert result.overall_score >= 1


@patch("agent.critic._get_client")
def test_schema_correction_retry(mock_get_client):
    """On first call return invalid JSON; second call (schema correction) returns valid JSON."""
    mock_client = MagicMock()
    invalid_response = MagicMock()
    invalid_response.content = [MagicMock(text="not valid json {{{")]

    valid_response = MagicMock()
    valid_response.content = [MagicMock(text=json.dumps(MOCK_CRITIQUE_VALID))]

    mock_client.messages.create.side_effect = [invalid_response, valid_response]
    mock_get_client.return_value = mock_client

    result = critique_ad(ECOMMERCE_INPUT)
    assert isinstance(result, AdCritique)
    assert mock_client.messages.create.call_count == 2
