from __future__ import annotations

SYSTEM_PROMPT = """You are a senior creative strategist and performance marketing expert with deep experience
in digital advertising across search, display, social, and native formats.

You critique ad copy the way a seasoned creative director and a performance marketer
would together — balancing brand voice with conversion outcomes.

Your critique must be:
- SPECIFIC: "The headline is weak" is not feedback. "The headline 'Grow Your Business'
  is a generic claim used by thousands of advertisers — it gives the audience no reason
  to stop scrolling" is feedback.
- ACTIONABLE: Every identified issue must have a concrete fix.
- PERFORMANCE-AWARE: Always connect creative observations to business outcomes.
  Weak CTA = lower CTR = higher CPC. Say this explicitly.
- PLATFORM-INTELLIGENT: Google Search copy must include keywords and be intent-matched.
  LinkedIn copy must be professional and insight-led. Facebook copy must hook in line 1.
  Native copy must not feel like an ad. Know the difference.
- HONEST: If the copy is strong, say so. Don't invent problems to seem thorough.

Domain rules to apply:
- Any headline that could describe any product in the category = generic, score Clarity max 4
- CTAs like "Learn More" or "Click Here" = weak, score CTA Strength max 3
- Superlatives without proof ("best", "leading", "world-class") = credibility risk, flag it
- Google Search copy without a keyword = likely quality score issue, flag it
- LinkedIn B2B copy that leads with features not outcomes = audience mismatch, flag it
- Copy that exceeds character limits = automatic flag, do not ignore

Respond ONLY with valid JSON matching the output schema. No preamble, no markdown fences."""

SCHEMA_CORRECTION_PROMPT = """Your previous response did not match the required JSON schema.

Please respond again with ONLY valid JSON that exactly matches this schema:
{
  "overall_score": <integer 1-100>,
  "overall_verdict": <"strong" | "needs_work" | "weak" | "do_not_run">,
  "executive_summary": <string, 2-3 sentences>,
  "dimensions": [
    {
      "dimension": <string>,
      "score": <integer 1-10>,
      "verdict": <string, one sentence>,
      "issue": <string or null>,
      "fix": <string or null>
    }
  ],
  "critical_issues": [<string>],
  "minor_issues": [<string>],
  "strengths": [<string>],
  "variants": [
    {
      "label": <string>,
      "headline": <string>,
      "body": <string or null>,
      "cta": <string or null>,
      "rationale": <string>
    }
  ],
  "ab_test_recommendation": <string>,
  "platform_fit_note": <string>
}

Rules:
- overall_score must be 1-100
- overall_verdict must be "do_not_run" only when overall_score < 25
- variants must contain exactly 2 or 3 items
- No markdown fences, no preamble, valid JSON only"""

COMPETITOR_SYSTEM_PROMPT = """You are a senior competitive intelligence analyst specialising in digital advertising.
You compare ad copy across competitors and identify differentiation gaps with precision.

Respond ONLY with valid JSON matching the schema provided. No preamble, no markdown fences."""

BRAND_VOICE_SYSTEM_PROMPT = """You are a brand compliance specialist. You assess ad copy against a brand voice profile
for tone, persona, and style compliance. You are precise about violations and constructive in suggestions.

Respond ONLY with valid JSON matching the schema provided. No preamble, no markdown fences."""

LOCALISATION_SYSTEM_PROMPT = """You are a localisation strategist with expertise in international advertising.
You assess ad copy for localisation readiness — idioms, cultural references, regulatory risks, and CTA norms.

Respond ONLY with valid JSON matching the schema provided. No preamble, no markdown fences."""


def build_user_prompt(ad_input: dict) -> str:
    parts = ["Critique the following ad copy:\n"]

    parts.append(f"HEADLINE: {ad_input['headline']}")

    if ad_input.get("body"):
        parts.append(f"BODY: {ad_input['body']}")

    if ad_input.get("cta"):
        parts.append(f"CTA: {ad_input['cta']}")

    if ad_input.get("tagline"):
        parts.append(f"TAGLINE: {ad_input['tagline']}")

    parts.append(f"\nCAMPAIGN CONTEXT:")
    parts.append(f"Platform: {ad_input['platform']}")
    parts.append(f"Target Audience: {ad_input['target_audience']}")
    parts.append(f"Campaign Goal: {ad_input['campaign_goal']}")
    parts.append(f"Product Category: {ad_input['product_category']}")

    if ad_input.get("usp"):
        parts.append(f"USP: {ad_input['usp']}")

    if ad_input.get("competitor_copy"):
        parts.append(f"Competitor Copy for Comparison: {ad_input['competitor_copy']}")

    if ad_input.get("character_limits"):
        parts.append(f"Character Limits: {ad_input['character_limits']}")

    parts.append(
        "\nScore dimensions: Clarity (15%), Audience Fit (15%), CTA Strength (15%), "
        "Value Proposition (20%), Emotional Hook (10%), Platform Fit (10%), "
        "Credibility (10%), Brevity (5%)."
    )
    parts.append("Provide exactly 2-3 improved variants.")

    return "\n".join(parts)


def build_competitor_prompt(your_ad: dict, competitors: list[dict], your_dimension_scores: dict[str, int]) -> str:
    parts = [
        "Perform a competitor gap analysis for the following ad.\n",
        "YOUR AD:",
        f"Headline: {your_ad['headline']}",
    ]
    if your_ad.get("body"):
        parts.append(f"Body: {your_ad['body']}")
    if your_ad.get("cta"):
        parts.append(f"CTA: {your_ad['cta']}")
    parts.append(f"Platform: {your_ad['platform']} | Category: {your_ad['product_category']}")
    parts.append(f"\nYOUR DIMENSION SCORES (from prior critique): {your_dimension_scores}")

    parts.append(f"\nCOMPETITOR ADS ({len(competitors)} total):")
    for i, c in enumerate(competitors, 1):
        parts.append(f"\n[Competitor {i}: {c['name']}]")
        parts.append(f"Headline: {c['headline']}")
        if c.get("body"):
            parts.append(f"Body: {c['body']}")
        if c.get("cta"):
            parts.append(f"CTA: {c['cta']}")

    parts.append("""
Return ONLY valid JSON matching this schema:
{
  "your_ad_summary": <string — 1-2 sentence assessment of your ad's positioning>,
  "differentiation_score": <integer 0-10 — how unique your positioning is vs field>,
  "gaps": [
    {
      "dimension": <string — one of the 8 scoring dimensions>,
      "your_score": <integer 1-10>,
      "competitor_avg": <float>,
      "gap": <float — your_score minus competitor_avg>,
      "verdict": <"ahead" | "behind" | "parity">
    }
  ],
  "category_cliches": [<string — phrases used by multiple competitors>],
  "unique_angles_available": [<string — angles no competitor is using>],
  "recommendation": <string — concrete action to improve differentiation>
}""")
    return "\n".join(parts)


def build_brand_voice_prompt(ad_input: dict, voice_profile: dict) -> str:
    parts = [
        f"Assess this ad copy for brand voice compliance with {voice_profile['brand_name']}'s guidelines.\n",
        "AD COPY:",
        f"Headline: {ad_input['headline']}",
    ]
    if ad_input.get("body"):
        parts.append(f"Body: {ad_input['body']}")
    if ad_input.get("cta"):
        parts.append(f"CTA: {ad_input['cta']}")

    parts.append(f"\nBRAND VOICE PROFILE:")
    parts.append(f"Required Tone: {voice_profile['required_tone']}")
    if voice_profile.get("persona"):
        parts.append(f"Persona: {voice_profile['persona']}")
    if voice_profile.get("notes"):
        parts.append(f"Additional Notes: {voice_profile['notes']}")
    if voice_profile.get("example_good_copy"):
        parts.append("Examples of ON-BRAND copy:")
        for ex in voice_profile["example_good_copy"]:
            parts.append(f'  - "{ex}"')
    if voice_profile.get("example_bad_copy"):
        parts.append("Examples of OFF-BRAND copy:")
        for ex in voice_profile["example_bad_copy"]:
            parts.append(f'  - "{ex}"')

    parts.append("""
Assess TONE and PERSONA compliance only (prohibited word violations are handled separately).

Return ONLY valid JSON matching this schema:
{
  "compliant": <boolean>,
  "compliance_score": <integer 0-100>,
  "violations": [
    {
      "field": <"headline" | "body" | "cta" | "tagline">,
      "text": <string — the offending text>,
      "rule": <string — which tone/persona rule is violated>,
      "severity": <"critical" | "moderate" | "low">
    }
  ],
  "suggestions": [<string — specific rewrite suggestions>],
  "voice_summary": <string — 1-2 sentence overall assessment>
}""")
    return "\n".join(parts)


def build_localisation_prompt(ad_input: dict, target_locale: str) -> str:
    parts = [
        f"Assess the localisation readiness of this ad copy for the locale: {target_locale}\n",
        "AD COPY:",
        f"Headline: {ad_input['headline']}",
    ]
    if ad_input.get("body"):
        parts.append(f"Body: {ad_input['body']}")
    if ad_input.get("cta"):
        parts.append(f"CTA: {ad_input['cta']}")
    parts.append(f"Platform: {ad_input['platform']} | Category: {ad_input['product_category']}")

    parts.append(f"""
Assess:
1. Idioms or cultural references that won't translate
2. CTA appropriateness for {target_locale} market norms
3. Regulatory risks (e.g. financial claims, health claims in this market)
4. Translation difficulty (word count, sentence structure, brand terms)
5. Locale-specific rewrite suggestions

Return ONLY valid JSON matching this schema:
{{
  "target_locale": "{target_locale}",
  "readiness_score": <integer 0-100>,
  "risks": [
    {{
      "element": <string — the specific phrase or element>,
      "risk": <string — why it's a risk>,
      "severity": <"critical" | "moderate" | "low">
    }}
  ],
  "translation_difficulty": <"easy" | "moderate" | "hard">,
  "locale_specific_suggestions": [<string>],
  "summary": <string — 1-2 sentence overall readiness assessment>
}}""")
    return "\n".join(parts)
