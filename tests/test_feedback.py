"""Tests for the performance feedback loop — no LLM calls."""

from __future__ import annotations

import pytest

from agent.feedback import (
    clear_feedback,
    get_dimension_insights,
    get_feedback,
    list_feedback,
    record_feedback,
)
from agent.models import FeedbackRecord, PerformanceMetrics


@pytest.fixture(autouse=True)
def reset_store():
    clear_feedback()
    yield
    clear_feedback()


def _make_record(
    critique_id: str = "test-001",
    headline: str = "Test Ad",
    platform: str = "facebook",
    category: str = "D2C skincare",
    score: int = 75,
    dim_scores: dict | None = None,
    ctr: float | None = 0.03,
) -> FeedbackRecord:
    return record_feedback(
        critique_id=critique_id,
        headline=headline,
        platform=platform,
        product_category=category,
        overall_score=score,
        dimension_scores=dim_scores or {"Clarity": 8, "CTA Strength": 7, "Emotional Hook": 9},
        metrics=PerformanceMetrics(ctr=ctr, conversion_rate=0.02, roas=3.5),
    )


def test_record_and_retrieve():
    record = _make_record("id-001", headline="Test headline")
    retrieved = get_feedback("id-001")
    assert retrieved is not None
    assert retrieved.headline == "Test headline"
    assert retrieved.overall_score == 75


def test_list_feedback_returns_all():
    _make_record("id-001")
    _make_record("id-002", headline="Second ad")
    records = list_feedback()
    assert len(records) == 2


def test_record_overwrites_same_id():
    _make_record("id-001", score=70)
    _make_record("id-001", score=85)
    assert get_feedback("id-001").overall_score == 85
    assert len(list_feedback()) == 1


def test_insights_empty_store():
    result = get_dimension_insights()
    assert result.sample_size == 0
    assert result.most_predictive_dimensions == []
    assert "No feedback records" in result.insight_summary


def test_insights_sample_size_correct():
    _make_record("id-001")
    _make_record("id-002")
    result = get_dimension_insights()
    assert result.sample_size == 2


def test_insights_predictive_dimensions_detected():
    # High Clarity score → high CTR
    _make_record("id-001", dim_scores={"Clarity": 9, "CTA Strength": 3}, ctr=0.08)
    _make_record("id-002", dim_scores={"Clarity": 9, "CTA Strength": 4}, ctr=0.09)
    # Low Clarity score → low CTR
    _make_record("id-003", dim_scores={"Clarity": 3, "CTA Strength": 8}, ctr=0.01)
    _make_record("id-004", dim_scores={"Clarity": 3, "CTA Strength": 7}, ctr=0.02)

    result = get_dimension_insights()
    assert "Clarity" in result.most_predictive_dimensions


def test_insights_weakest_for_category():
    _make_record("id-001", category="SaaS", dim_scores={"Clarity": 8, "CTA Strength": 3, "Credibility": 4})
    _make_record("id-002", category="SaaS", dim_scores={"Clarity": 7, "CTA Strength": 4, "Credibility": 3})
    result = get_dimension_insights()
    assert "SaaS" in result.weakest_for_category
    # CTA Strength or Credibility should be weakest (both low)
    assert result.weakest_for_category["SaaS"] in {"CTA Strength", "Credibility"}


def test_insights_no_ctr_data_returns_insufficient():
    _make_record("id-001", ctr=None)
    _make_record("id-002", ctr=None)
    result = get_dimension_insights()
    assert result.most_predictive_dimensions == [] or "insufficient" in result.insight_summary


def test_clear_feedback():
    _make_record("id-001")
    _make_record("id-002")
    clear_feedback()
    assert len(list_feedback()) == 0
    assert get_feedback("id-001") is None


def test_recorded_at_is_set():
    record = _make_record("id-001")
    assert record.recorded_at is not None
    assert "2026" in record.recorded_at or "T" in record.recorded_at
