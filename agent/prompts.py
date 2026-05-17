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
