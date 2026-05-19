from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from .models import DimensionInsights, FeedbackRecord, PerformanceMetrics

_STORE: dict[str, FeedbackRecord] = {}
_STORE_PATH: str | None = os.getenv("FEEDBACK_STORE_PATH")


def _load_store() -> None:
    global _STORE
    if _STORE_PATH and os.path.exists(_STORE_PATH):
        with open(_STORE_PATH) as f:
            data = json.load(f)
        _STORE = {k: FeedbackRecord(**v) for k, v in data.items()}


def _save_store() -> None:
    if _STORE_PATH:
        with open(_STORE_PATH, "w") as f:
            json.dump({k: v.model_dump() for k, v in _STORE.items()}, f, indent=2)


def record_feedback(
    critique_id: str,
    headline: str,
    platform: str,
    product_category: str,
    overall_score: int,
    dimension_scores: dict[str, int],
    metrics: PerformanceMetrics,
) -> FeedbackRecord:
    record = FeedbackRecord(
        critique_id=critique_id,
        headline=headline,
        platform=platform,
        product_category=product_category,
        overall_score=overall_score,
        dimension_scores=dimension_scores,
        metrics=metrics,
        recorded_at=datetime.now(timezone.utc).isoformat(),
    )
    _STORE[critique_id] = record
    _save_store()
    return record


def get_feedback(critique_id: str) -> FeedbackRecord | None:
    return _STORE.get(critique_id)


def list_feedback() -> list[FeedbackRecord]:
    return list(_STORE.values())


def clear_feedback() -> None:
    _STORE.clear()
    if _STORE_PATH and os.path.exists(_STORE_PATH):
        os.remove(_STORE_PATH)


def get_dimension_insights() -> DimensionInsights:
    records = list(_STORE.values())
    if not records:
        return DimensionInsights(
            most_predictive_dimensions=[],
            weakest_for_category={},
            insight_summary="No feedback records yet. Record performance metrics to enable insights.",
            sample_size=0,
        )

    # For each dimension, find whether high scores (>=7) correlate with higher CTR
    dim_ctr_pairs: dict[str, list[tuple[int, float]]] = {}
    for record in records:
        if record.metrics.ctr is None:
            continue
        for dim, score in record.dimension_scores.items():
            dim_ctr_pairs.setdefault(dim, []).append((score, record.metrics.ctr))

    predictive: list[str] = []
    for dim, pairs in dim_ctr_pairs.items():
        if len(pairs) < 2:
            continue
        high_score_ctrs = [ctr for score, ctr in pairs if score >= 7]
        low_score_ctrs = [ctr for score, ctr in pairs if score < 7]
        if high_score_ctrs and low_score_ctrs:
            avg_high = sum(high_score_ctrs) / len(high_score_ctrs)
            avg_low = sum(low_score_ctrs) / len(low_score_ctrs)
            if avg_high > avg_low * 1.1:
                predictive.append(dim)

    # Weakest dimension per product category
    cat_dim_scores: dict[str, dict[str, list[int]]] = {}
    for record in records:
        for dim, score in record.dimension_scores.items():
            cat_dim_scores.setdefault(record.product_category, {}).setdefault(dim, []).append(score)

    weakest_for_category: dict[str, str] = {}
    for cat, dims in cat_dim_scores.items():
        if dims:
            weakest_for_category[cat] = min(
                dims,
                key=lambda d: sum(dims[d]) / len(dims[d]),
            )

    summary = (
        f"Analysis of {len(records)} feedback records. "
        f"Most CTR-predictive dimensions: {', '.join(predictive) if predictive else 'insufficient data (need CTR metrics)'}. "
        f"Categories tracked: {len(weakest_for_category)}."
    )

    return DimensionInsights(
        most_predictive_dimensions=predictive,
        weakest_for_category=weakest_for_category,
        insight_summary=summary,
        sample_size=len(records),
    )


_load_store()
