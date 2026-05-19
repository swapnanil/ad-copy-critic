from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class AdCopyInput(BaseModel):
    headline: str
    body: str | None = None
    cta: str | None = None
    tagline: str | None = None

    platform: Literal[
        "google_search",
        "google_display",
        "facebook",
        "instagram",
        "linkedin",
        "native",
        "programmatic_display",
        "email",
        "other",
    ]
    target_audience: str
    campaign_goal: Literal[
        "awareness",
        "consideration",
        "lead_generation",
        "conversion",
        "retention",
        "app_install",
    ]
    product_category: str
    usp: str | None = None
    competitor_copy: str | None = None
    character_limits: dict | None = None


class DimensionScore(BaseModel):
    dimension: str
    score: int
    verdict: str
    issue: str | None = None
    fix: str | None = None


class AdVariant(BaseModel):
    label: str
    headline: str
    body: str | None = None
    cta: str | None = None
    rationale: str


class AdCritique(BaseModel):
    overall_score: int
    overall_verdict: Literal["strong", "needs_work", "weak", "do_not_run"]
    executive_summary: str

    dimensions: list[DimensionScore]

    critical_issues: list[str]
    minor_issues: list[str]

    strengths: list[str]

    variants: list[AdVariant]

    ab_test_recommendation: str
    platform_fit_note: str

    slack_summary: str | None = None


class BatchCritique(BaseModel):
    critiques: list[AdCritique]
    fleet_summary: str
    average_score: float
    weakest_dimension: str


# ── Feature 1: Performance Feedback Loop ──────────────────────────────────────

class PerformanceMetrics(BaseModel):
    ctr: float | None = None
    conversion_rate: float | None = None
    roas: float | None = None
    impressions: int | None = None
    clicks: int | None = None
    spend: float | None = None


class FeedbackRecord(BaseModel):
    critique_id: str
    headline: str
    platform: str
    product_category: str
    overall_score: int
    dimension_scores: dict[str, int]
    metrics: PerformanceMetrics
    recorded_at: str


class DimensionInsights(BaseModel):
    most_predictive_dimensions: list[str]
    weakest_for_category: dict[str, str]
    insight_summary: str
    sample_size: int


# ── Feature 2: Competitor Gap Analysis ────────────────────────────────────────

class CompetitorAd(BaseModel):
    name: str
    headline: str
    body: str | None = None
    cta: str | None = None


class DimensionGap(BaseModel):
    dimension: str
    your_score: int
    competitor_avg: float
    gap: float
    verdict: Literal["ahead", "behind", "parity"]


class CompetitorAnalysis(BaseModel):
    your_ad_summary: str
    differentiation_score: int
    gaps: list[DimensionGap]
    category_cliches: list[str]
    unique_angles_available: list[str]
    recommendation: str


# ── Feature 3: Brand Voice Compliance ─────────────────────────────────────────

class BrandVoiceProfile(BaseModel):
    brand_name: str
    prohibited_words: list[str] = []
    required_tone: str
    persona: str | None = None
    example_good_copy: list[str] = []
    example_bad_copy: list[str] = []
    notes: str | None = None


class VoiceViolation(BaseModel):
    field: Literal["headline", "body", "cta", "tagline"]
    text: str
    rule: str
    severity: Literal["critical", "moderate", "low"]


class BrandVoiceResult(BaseModel):
    compliant: bool
    compliance_score: int
    violations: list[VoiceViolation]
    suggestions: list[str]
    voice_summary: str


# ── Feature 5: Localisation Readiness ─────────────────────────────────────────

class LocalisationRisk(BaseModel):
    element: str
    risk: str
    severity: Literal["critical", "moderate", "low"]


class LocalisationResult(BaseModel):
    target_locale: str
    readiness_score: int
    risks: list[LocalisationRisk]
    translation_difficulty: Literal["easy", "moderate", "hard"]
    locale_specific_suggestions: list[str]
    summary: str


# ── Feature 6: Trend Benchmarking ─────────────────────────────────────────────

class TrendBenchmark(BaseModel):
    platform: str
    product_category: str
    above_average_dimensions: list[str]
    below_average_dimensions: list[str]
    percentile_estimate: int
    benchmark_note: str
