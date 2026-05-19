"""Tests for Slack summary generation — no LLM calls needed."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agent import AdCopyInput, AdCritique, critique_ad
from agent.critic import _format_slack_summary

MOCK_CRITIQUE = {
    "overall_score": 72,
    "overall_verdict": "strong",
    "executive_summary": "This ad demonstrates strong clarity and platform fit.",
    "dimensions": [
        {"dimension": "Clarity", "score": 8, "verdict": "Clear.", "issue": None, "fix": None},
        {"dimension": "Audience Fit", "score": 7, "verdict": "Well targeted.", "issue": None, "fix": None},
        {"dimension": "CTA Strength", "score": 7, "verdict": "Action-oriented.", "issue": None, "fix": None},
        {"dimension": "Value Proposition", "score": 8, "verdict": "Differentiators explicit.", "issue": None, "fix": None},
        {"dimension": "Emotional Hook", "score": 7, "verdict": "Hooks on frustration.", "issue": None, "fix": None},
        {"dimension": "Platform Fit", "score": 7, "verdict": "Appropriate.", "issue": None, "fix": None},
        {"dimension": "Credibility", "score": 6, "verdict": "Needs proof.", "issue": "Unverified superlative.", "fix": "Add stat."},
        {"dimension": "Brevity", "score": 6, "verdict": "Slightly verbose.", "issue": None, "fix": None},
    ],
    "critical_issues": [],
    "minor_issues": ["Body slightly long."],
    "strengths": ["Strong hook.", "Clear value proposition."],
    "variants": [
        {"label": "Variant A", "headline": "Improved Headline A", "body": None, "cta": "Get Started Free", "rationale": "More benefit-led."},
        {"label": "Variant B", "headline": "Improved Headline B", "body": None, "cta": "Try It Now", "rationale": "Social proof framing."},
    ],
    "ab_test_recommendation": "Run Variant A vs control for 7 days.",
    "platform_fit_note": "Good platform fit.",
}

AD_INPUT = AdCopyInput(
    headline="Finally, Sunscreen That Doesn't Feel Like Sunscreen",
    body="Ultra-light SPF 50.",
    cta="Shop Now",
    platform="facebook",
    target_audience="Women 25-40",
    campaign_goal="conversion",
    product_category="D2C skincare",
)


def _make_mock_client(response: dict):
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps(response))]
    mock_client.messages.create.return_value = mock_resp
    return mock_client


def test_slack_summary_present_after_critique():
    with patch("agent.critic._get_client", return_value=_make_mock_client(MOCK_CRITIQUE)):
        result = critique_ad(AD_INPUT)
    assert result.slack_summary is not None
    assert len(result.slack_summary.strip()) > 0


def test_slack_summary_contains_score():
    with patch("agent.critic._get_client", return_value=_make_mock_client(MOCK_CRITIQUE)):
        result = critique_ad(AD_INPUT)
    assert "72" in result.slack_summary
    assert "100" in result.slack_summary


def test_slack_summary_contains_verdict():
    with patch("agent.critic._get_client", return_value=_make_mock_client(MOCK_CRITIQUE)):
        result = critique_ad(AD_INPUT)
    assert "STRONG" in result.slack_summary.upper()


def test_slack_summary_contains_headline():
    with patch("agent.critic._get_client", return_value=_make_mock_client(MOCK_CRITIQUE)):
        result = critique_ad(AD_INPUT)
    assert "Sunscreen" in result.slack_summary


def test_slack_summary_contains_top_strength():
    critique = AdCritique(**MOCK_CRITIQUE)
    summary = _format_slack_summary(critique, "Test Headline")
    assert "Strong hook." in summary


def test_slack_summary_contains_best_variant():
    critique = AdCritique(**MOCK_CRITIQUE)
    summary = _format_slack_summary(critique, "Test Headline")
    assert "Improved Headline A" in summary


def test_slack_summary_do_not_run_verdict():
    dnr_critique = {
        **MOCK_CRITIQUE,
        "overall_score": 20,
        "overall_verdict": "do_not_run",
        "critical_issues": ["No clear value proposition."],
        "strengths": [],
    }
    critique = AdCritique(**dnr_critique)
    summary = _format_slack_summary(critique, "Bad Ad Headline")
    assert "DO NOT RUN" in summary.upper() or "no_entry" in summary


def test_slack_summary_no_critical_shows_minor():
    critique_no_critical = {**MOCK_CRITIQUE, "critical_issues": [], "minor_issues": ["Body slightly long."]}
    critique = AdCritique(**critique_no_critical)
    summary = _format_slack_summary(critique, "Test")
    assert "Body slightly long." in summary


def test_slack_summary_no_issues_shows_none():
    clean_critique = {**MOCK_CRITIQUE, "critical_issues": [], "minor_issues": []}
    critique = AdCritique(**clean_critique)
    summary = _format_slack_summary(critique, "Test")
    assert "None" in summary
