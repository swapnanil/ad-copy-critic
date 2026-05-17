from __future__ import annotations

import json
import os
import time

import anthropic

from .models import AdCopyInput, AdCritique, BatchCritique
from .prompts import SCHEMA_CORRECTION_PROMPT, SYSTEM_PROMPT, build_user_prompt

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


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _call_api(client: anthropic.Anthropic, messages: list[dict]) -> str:
    """Call the Anthropic API with exponential backoff on rate limits."""
    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
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
    """Parse JSON response, retrying once with schema correction on failure."""
    try:
        data = json.loads(raw)
        return AdCritique(**data)
    except (json.JSONDecodeError, Exception):
        # Retry once with schema correction prompt
        user_prompt = build_user_prompt(ad_input.model_dump())
        correction_messages = [
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": raw},
            {"role": "user", "content": SCHEMA_CORRECTION_PROMPT},
        ]
        corrected_raw = _call_api(client, correction_messages)
        data = json.loads(corrected_raw)
        return AdCritique(**data)


def critique_ad(ad_input: AdCopyInput) -> AdCritique:
    """Run a single ad critique."""
    if not ad_input.headline.strip():
        raise ValueError("Headline cannot be empty. Please provide a headline to critique.")

    client = _get_client()
    user_prompt = build_user_prompt(ad_input.model_dump())
    messages = [{"role": "user", "content": user_prompt}]

    raw = _call_api(client, messages)
    critique = _parse_critique(raw, ad_input, client)

    # Enforce business rules
    if critique.overall_score < 25 and critique.overall_verdict != "do_not_run":
        critique.overall_verdict = "do_not_run"
    if critique.overall_score >= 25 and critique.overall_verdict == "do_not_run":
        critique.overall_verdict = "weak"

    # Ensure 2-3 variants
    if len(critique.variants) < 2 or len(critique.variants) > 3:
        raise ValueError(
            f"Expected 2-3 variants, got {len(critique.variants)}. Please retry."
        )

    # Flag character limit violations
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

    return critique


def critique_batch(ads: list[AdCopyInput]) -> BatchCritique:
    """Critique multiple ads and produce a fleet summary."""
    critiques = [critique_ad(ad) for ad in ads]

    avg_score = sum(c.overall_score for c in critiques) / len(critiques)

    # Find weakest dimension across all ads
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
