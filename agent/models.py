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


class BatchCritique(BaseModel):
    critiques: list[AdCritique]
    fleet_summary: str
    average_score: float
    weakest_dimension: str
