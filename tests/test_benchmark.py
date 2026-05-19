"""Tests for trend benchmarking — purely rule-based, no LLM calls."""

from __future__ import annotations

import pytest

from agent import AdCritique, TrendBenchmark, benchmark_against_trends

STRONG_CRITIQUE = AdCritique(
    overall_score=85,
    overall_verdict="strong",
    executive_summary="Excellent ad.",
    dimensions=[
        {"dimension": "Clarity", "score": 9, "verdict": "Very clear.", "issue": None, "fix": None},
        {"dimension": "Audience Fit", "score": 8, "verdict": "Well targeted.", "issue": None, "fix": None},
        {"dimension": "CTA Strength", "score": 8, "verdict": "Strong CTA.", "issue": None, "fix": None},
        {"dimension": "Value Proposition", "score": 9, "verdict": "Compelling.", "issue": None, "fix": None},
        {"dimension": "Emotional Hook", "score": 8, "verdict": "Good hook.", "issue": None, "fix": None},
        {"dimension": "Platform Fit", "score": 8, "verdict": "Great fit.", "issue": None, "fix": None},
        {"dimension": "Credibility", "score": 7, "verdict": "Credible.", "issue": None, "fix": None},
        {"dimension": "Brevity", "score": 8, "verdict": "Concise.", "issue": None, "fix": None},
    ],
    critical_issues=[],
    minor_issues=[],
    strengths=["Everything is strong."],
    variants=[
        {"label": "A", "headline": "V A", "body": None, "cta": None, "rationale": "Better."},
        {"label": "B", "headline": "V B", "body": None, "cta": None, "rationale": "Alt."},
    ],
    ab_test_recommendation="Test both.",
    platform_fit_note="Excellent.",
)

WEAK_CRITIQUE = AdCritique(
    **{**STRONG_CRITIQUE.model_dump(), "overall_score": 35, "overall_verdict": "weak",
       "dimensions": [
           {"dimension": "Clarity", "score": 3, "verdict": "Unclear.", "issue": "Vague.", "fix": "Specify."},
           {"dimension": "Audience Fit", "score": 3, "verdict": "Off target.", "issue": None, "fix": None},
           {"dimension": "CTA Strength", "score": 2, "verdict": "Weak CTA.", "issue": None, "fix": None},
           {"dimension": "Value Proposition", "score": 3, "verdict": "Weak USP.", "issue": None, "fix": None},
           {"dimension": "Emotional Hook", "score": 4, "verdict": "No hook.", "issue": None, "fix": None},
           {"dimension": "Platform Fit", "score": 3, "verdict": "Poor fit.", "issue": None, "fix": None},
           {"dimension": "Credibility", "score": 3, "verdict": "Untrustworthy.", "issue": None, "fix": None},
           {"dimension": "Brevity", "score": 4, "verdict": "Verbose.", "issue": None, "fix": None},
       ]}
)


def test_benchmark_returns_correct_type():
    result = benchmark_against_trends(STRONG_CRITIQUE, "facebook", "D2C skincare")
    assert isinstance(result, TrendBenchmark)


def test_strong_ad_above_average_dimensions():
    result = benchmark_against_trends(STRONG_CRITIQUE, "facebook", "D2C skincare")
    assert len(result.above_average_dimensions) > 0


def test_weak_ad_below_average_dimensions():
    result = benchmark_against_trends(WEAK_CRITIQUE, "facebook", "D2C skincare")
    assert len(result.below_average_dimensions) > 0


def test_percentile_in_valid_range():
    result = benchmark_against_trends(STRONG_CRITIQUE, "linkedin", "B2B fintech")
    assert 1 <= result.percentile_estimate <= 99


def test_strong_ad_higher_percentile_than_weak():
    strong_result = benchmark_against_trends(STRONG_CRITIQUE, "google_search", "SaaS")
    weak_result = benchmark_against_trends(WEAK_CRITIQUE, "google_search", "SaaS")
    assert strong_result.percentile_estimate > weak_result.percentile_estimate


def test_platform_preserved_in_result():
    result = benchmark_against_trends(STRONG_CRITIQUE, "instagram", "Fashion")
    assert result.platform == "instagram"
    assert result.product_category == "Fashion"


def test_benchmark_note_contains_platform():
    result = benchmark_against_trends(STRONG_CRITIQUE, "linkedin", "B2B SaaS")
    assert "linkedin" in result.benchmark_note


def test_unknown_platform_uses_defaults():
    result = benchmark_against_trends(STRONG_CRITIQUE, "tiktok", "Entertainment")
    assert isinstance(result.above_average_dimensions, list)
    assert isinstance(result.below_average_dimensions, list)


def test_no_llm_calls_needed(monkeypatch):
    import agent.critic as critic_mod
    calls = []
    monkeypatch.setattr(critic_mod, "_get_client", lambda: calls.append(1) or None)
    benchmark_against_trends(STRONG_CRITIQUE, "facebook", "skincare")
    assert len(calls) == 0
