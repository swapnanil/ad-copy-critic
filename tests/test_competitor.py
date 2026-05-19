"""Tests for competitor gap analysis."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agent import AdCopyInput, AdCritique, CompetitorAd, CompetitorAnalysis, compare_competitors

YOUR_AD = AdCopyInput(
    headline="Finally, Sunscreen That Doesn't Feel Like Sunscreen",
    body="Ultra-light SPF 50 that disappears into skin in seconds.",
    cta="Shop Now — Free Shipping Over $40",
    platform="facebook",
    target_audience="Women 25-40 interested in skincare",
    campaign_goal="conversion",
    product_category="D2C skincare",
    usp="Invisible finish, SPF 50, reef-safe",
)

YOUR_CRITIQUE = AdCritique(
    overall_score=72,
    overall_verdict="strong",
    executive_summary="Strong positioning with a clear differentiator.",
    dimensions=[
        {"dimension": "Clarity", "score": 8, "verdict": "Clear.", "issue": None, "fix": None},
        {"dimension": "Audience Fit", "score": 7, "verdict": "Well targeted.", "issue": None, "fix": None},
        {"dimension": "CTA Strength", "score": 7, "verdict": "Action-oriented.", "issue": None, "fix": None},
        {"dimension": "Value Proposition", "score": 8, "verdict": "Strong USP.", "issue": None, "fix": None},
        {"dimension": "Emotional Hook", "score": 7, "verdict": "Good hook.", "issue": None, "fix": None},
        {"dimension": "Platform Fit", "score": 7, "verdict": "Appropriate.", "issue": None, "fix": None},
        {"dimension": "Credibility", "score": 6, "verdict": "Needs proof.", "issue": None, "fix": None},
        {"dimension": "Brevity", "score": 7, "verdict": "Concise.", "issue": None, "fix": None},
    ],
    critical_issues=[],
    minor_issues=[],
    strengths=["Strong USP."],
    variants=[
        {"label": "A", "headline": "Variant A", "body": None, "cta": None, "rationale": "Test."},
        {"label": "B", "headline": "Variant B", "body": None, "cta": None, "rationale": "Test."},
    ],
    ab_test_recommendation="Test A vs B.",
    platform_fit_note="Good fit.",
)

COMPETITORS = [
    CompetitorAd(name="SunCare Pro", headline="The Best Sunscreen on the Market", cta="Buy Now"),
    CompetitorAd(name="ShieldSPF", headline="SPF 50 Protection You Can Trust", body="Trusted by dermatologists.", cta="Shop Now"),
]

MOCK_ANALYSIS = {
    "your_ad_summary": "Strong differentiation via sensory benefit ('doesn't feel like sunscreen').",
    "differentiation_score": 8,
    "gaps": [
        {
            "dimension": "Clarity",
            "your_score": 8,
            "competitor_avg": 6.5,
            "gap": 1.5,
            "verdict": "ahead",
        },
        {
            "dimension": "Credibility",
            "your_score": 6,
            "competitor_avg": 7.0,
            "gap": -1.0,
            "verdict": "behind",
        },
    ],
    "category_cliches": ["SPF 50 Protection", "Trust"],
    "unique_angles_available": ["Reef-safe angle not used by competitors", "Reef ecosystem angle"],
    "recommendation": "Lean into reef-safe positioning — no competitor owns it.",
}


def _mock_client(response: dict):
    mock = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(response))]
    mock.messages.create.return_value = msg
    return mock


def test_compare_competitors_returns_analysis():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_ANALYSIS)):
        result = compare_competitors(YOUR_AD, COMPETITORS, YOUR_CRITIQUE)
    assert isinstance(result, CompetitorAnalysis)


def test_differentiation_score_in_range():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_ANALYSIS)):
        result = compare_competitors(YOUR_AD, COMPETITORS, YOUR_CRITIQUE)
    assert 0 <= result.differentiation_score <= 10


def test_gaps_contain_dimension_verdicts():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_ANALYSIS)):
        result = compare_competitors(YOUR_AD, COMPETITORS, YOUR_CRITIQUE)
    verdicts = {g.verdict for g in result.gaps}
    assert verdicts.issubset({"ahead", "behind", "parity"})


def test_category_cliches_is_list():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_ANALYSIS)):
        result = compare_competitors(YOUR_AD, COMPETITORS, YOUR_CRITIQUE)
    assert isinstance(result.category_cliches, list)


def test_unique_angles_is_list():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_ANALYSIS)):
        result = compare_competitors(YOUR_AD, COMPETITORS, YOUR_CRITIQUE)
    assert isinstance(result.unique_angles_available, list)
    assert len(result.unique_angles_available) >= 1


def test_recommendation_is_non_empty():
    with patch("agent.critic._get_client", return_value=_mock_client(MOCK_ANALYSIS)):
        result = compare_competitors(YOUR_AD, COMPETITORS, YOUR_CRITIQUE)
    assert isinstance(result.recommendation, str)
    assert len(result.recommendation.strip()) > 0


def test_too_many_competitors_raises():
    too_many = [CompetitorAd(name=f"C{i}", headline=f"Ad {i}") for i in range(5)]
    with pytest.raises(ValueError, match="1-4 competitor"):
        compare_competitors(YOUR_AD, too_many, YOUR_CRITIQUE)


def test_zero_competitors_raises():
    with pytest.raises(ValueError, match="1-4 competitor"):
        compare_competitors(YOUR_AD, [], YOUR_CRITIQUE)
