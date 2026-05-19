from __future__ import annotations

import json
import os
import time

import anthropic

from .models import (
    AdCopyInput,
    AdCritique,
    BatchCritique,
    BrandVoiceProfile,
    BrandVoiceResult,
    CompetitorAd,
    CompetitorAnalysis,
    LocalisationResult,
    TrendBenchmark,
    VoiceViolation,
)
from .prompts import (
    BRAND_VOICE_SYSTEM_PROMPT,
    COMPETITOR_SYSTEM_PROMPT,
    LOCALISATION_SYSTEM_PROMPT,
    SCHEMA_CORRECTION_PROMPT,
    SYSTEM_PROMPT,
    build_brand_voice_prompt,
    build_competitor_prompt,
    build_localisation_prompt,
    build_user_prompt,
)

MODEL = os.getenv("MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))

DIMENSION_WEIGHTS = {
    "Clarity": 0.15,
    "Audience Fit": 0.15,
    "CTA Strength": 0.15,
    "Value Proposition": 0.20,
    "Emotional Hook": 0.10,
    "Platform Fit": 0.10,
    "Credibility": 0.10,
    "Brevity": 0.05,
}

# Industry baseline scores by platform (used for trend benchmarking)
_PLATFORM_BASELINES: dict[str, dict[str, int]] = {
    "google_search": {"Clarity": 6, "CTA Strength": 6, "Brevity": 7, "Platform Fit": 6, "Audience Fit": 6, "Value Proposition": 6, "Emotional Hook": 5, "Credibility": 6},
    "facebook": {"Emotional Hook": 7, "Clarity": 5, "CTA Strength": 6, "Brevity": 6, "Audience Fit": 6, "Value Proposition": 6, "Platform Fit": 6, "Credibility": 5},
    "linkedin": {"Audience Fit": 6, "Credibility": 7, "Value Proposition": 7, "Clarity": 6, "CTA Strength": 5, "Brevity": 5, "Emotional Hook": 5, "Platform Fit": 6},
    "instagram": {"Emotional Hook": 7, "Brevity": 7, "Platform Fit": 7, "Clarity": 5, "CTA Strength": 6, "Audience Fit": 6, "Value Proposition": 5, "Credibility": 5},
}
_DEFAULT_BASELINE: dict[str, int] = {"Clarity": 6, "Audience Fit": 6, "CTA Strength": 5, "Value Proposition": 6, "Emotional Hook": 6, "Platform Fit": 6, "Credibility": 5, "Brevity": 6}


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _call_api(client: anthropic.Anthropic, messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2**attempt)
            time.sleep(delay)

    raise RuntimeError("Max retries exceeded")


def _parse_critique(raw: str, ad_input: AdCopyInput, client: anthropic.Anthropic) -> AdCritique:
    try:
        data = json.loads(raw)
        return AdCritique(**data)
    except (json.JSONDecodeError, Exception):
        user_prompt = build_user_prompt(ad_input.model_dump())
        correction_messages = [
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": raw},
            {"role": "user", "content": SCHEMA_CORRECTION_PROMPT},
        ]
        corrected_raw = _call_api(client, correction_messages)
        data = json.loads(corrected_raw)
        return AdCritique(**data)


def _format_slack_summary(critique: AdCritique, headline: str) -> str:
    verdict_emoji = {
        "strong": ":white_check_mark:",
        "needs_work": ":warning:",
        "weak": ":x:",
        "do_not_run": ":no_entry:",
    }
    emoji = verdict_emoji.get(critique.overall_verdict, ":information_source:")
    verdict_display = critique.overall_verdict.upper().replace("_", " ")
    top_issue = (
        critique.critical_issues[0] if critique.critical_issues
        else critique.minor_issues[0] if critique.minor_issues
        else "None"
    )
    top_strength = critique.strengths[0] if critique.strengths else "—"
    best_variant = critique.variants[0] if critique.variants else None

    lines = [
        f"{emoji} *[{verdict_display}] {critique.overall_score}/100 — {headline[:60]}*",
        f"> {critique.executive_summary}",
        f":warning: Top issue: {top_issue}",
        f":white_check_mark: Top strength: {top_strength}",
    ]
    if best_variant:
        lines.append(f':bulb: Best variant: "{best_variant.headline}" — {best_variant.rationale}')
    return "\n".join(lines)


def critique_ad(ad_input: AdCopyInput) -> AdCritique:
    if not ad_input.headline.strip():
        raise ValueError("Headline cannot be empty. Please provide a headline to critique.")

    client = _get_client()
    user_prompt = build_user_prompt(ad_input.model_dump())
    messages = [{"role": "user", "content": user_prompt}]

    raw = _call_api(client, messages)
    critique = _parse_critique(raw, ad_input, client)

    if critique.overall_score < 25 and critique.overall_verdict != "do_not_run":
        critique.overall_verdict = "do_not_run"
    if critique.overall_score >= 25 and critique.overall_verdict == "do_not_run":
        critique.overall_verdict = "weak"

    if len(critique.variants) < 2 or len(critique.variants) > 3:
        raise ValueError(
            f"Expected 2-3 variants, got {len(critique.variants)}. Please retry."
        )

    if ad_input.character_limits:
        for field, limit in ad_input.character_limits.items():
            value = getattr(ad_input, field, None)
            if value and len(value) > limit:
                violation_msg = (
                    f"{field.capitalize()} exceeds character limit: "
                    f"{len(value)} chars vs {limit} limit."
                )
                if violation_msg not in critique.critical_issues:
                    critique.critical_issues.insert(0, violation_msg)

    critique.slack_summary = _format_slack_summary(critique, ad_input.headline)

    return critique


def critique_batch(ads: list[AdCopyInput]) -> BatchCritique:
    critiques = [critique_ad(ad) for ad in ads]

    avg_score = sum(c.overall_score for c in critiques) / len(critiques)

    dim_totals: dict[str, list[int]] = {}
    for critique in critiques:
        for dim in critique.dimensions:
            dim_totals.setdefault(dim.dimension, []).append(dim.score)

    weakest_dim = min(
        dim_totals,
        key=lambda d: sum(dim_totals[d]) / len(dim_totals[d]),
    )

    fleet_summary = (
        f"Batch of {len(critiques)} ads: average score {avg_score:.1f}/100. "
        f"Weakest area across the fleet: {weakest_dim}. "
        f"{sum(1 for c in critiques if c.overall_score >= 70)} ads scored 70+, "
        f"{sum(1 for c in critiques if c.overall_verdict == 'do_not_run')} flagged do_not_run."
    )

    return BatchCritique(
        critiques=critiques,
        fleet_summary=fleet_summary,
        average_score=round(avg_score, 1),
        weakest_dimension=weakest_dim,
    )


def compare_competitors(
    your_ad: AdCopyInput,
    competitors: list[CompetitorAd],
    your_critique: AdCritique,
) -> CompetitorAnalysis:
    if not competitors or len(competitors) > 4:
        raise ValueError("Provide 1-4 competitor ads.")

    client = _get_client()
    dim_scores = {d.dimension: d.score for d in your_critique.dimensions}
    prompt = build_competitor_prompt(
        your_ad.model_dump(),
        [c.model_dump() for c in competitors],
        dim_scores,
    )
    messages = [{"role": "user", "content": prompt}]
    raw = _call_api(client, messages, system=COMPETITOR_SYSTEM_PROMPT)
    data = json.loads(raw)
    return CompetitorAnalysis(**data)


def check_brand_voice(
    ad_input: AdCopyInput,
    voice_profile: BrandVoiceProfile,
) -> BrandVoiceResult:
    # Rule-based: prohibited word scan
    rule_violations: list[VoiceViolation] = []
    fields = {
        "headline": ad_input.headline,
        "body": ad_input.body,
        "cta": ad_input.cta,
        "tagline": ad_input.tagline,
    }
    for field_name, text in fields.items():
        if not text:
            continue
        for word in voice_profile.prohibited_words:
            if word.lower() in text.lower():
                rule_violations.append(VoiceViolation(
                    field=field_name,  # type: ignore[arg-type]
                    text=text,
                    rule=f'Prohibited word: "{word}"',
                    severity="critical",
                ))

    # LLM call for tone/persona compliance
    client = _get_client()
    prompt = build_brand_voice_prompt(ad_input.model_dump(), voice_profile.model_dump())
    messages = [{"role": "user", "content": prompt}]
    raw = _call_api(client, messages, system=BRAND_VOICE_SYSTEM_PROMPT)
    data = json.loads(raw)
    result = BrandVoiceResult(**data)

    # Merge: prepend rule-based violations
    result.violations = rule_violations + result.violations
    if rule_violations:
        result.compliant = False
        result.compliance_score = min(result.compliance_score, 50)

    return result


def check_localisation(ad_input: AdCopyInput, target_locale: str) -> LocalisationResult:
    client = _get_client()
    prompt = build_localisation_prompt(ad_input.model_dump(), target_locale)
    messages = [{"role": "user", "content": prompt}]
    raw = _call_api(client, messages, system=LOCALISATION_SYSTEM_PROMPT)
    data = json.loads(raw)
    return LocalisationResult(**data)


def benchmark_against_trends(
    critique: AdCritique,
    platform: str,
    product_category: str,
) -> TrendBenchmark:
    baselines = {**_DEFAULT_BASELINE, **_PLATFORM_BASELINES.get(platform, {})}
    dim_scores = {d.dimension: d.score for d in critique.dimensions}

    above = [d for d, score in dim_scores.items() if score > baselines.get(d, 6)]
    below = [d for d, score in dim_scores.items() if score < baselines.get(d, 6)]

    percentile = min(99, max(1, (critique.overall_score - 30) * 2))

    return TrendBenchmark(
        platform=platform,
        product_category=product_category,
        above_average_dimensions=above,
        below_average_dimensions=below,
        percentile_estimate=percentile,
        benchmark_note=(
            f"vs. {platform} industry baseline: {len(above)} dimensions above average, "
            f"{len(below)} below. Overall score of {critique.overall_score} is approximately "
            f"the {percentile}th percentile."
        ),
    )
