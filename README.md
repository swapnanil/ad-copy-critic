# ad-copy-critic

**[llm-tools](https://swapnanilsaha.com) suite by Swapnanil Saha**

Most ad feedback is vague ("make it punchier"), subjective, and arrives too late. **ad-copy-critic** scores every ad against 8 performance dimensions with the specificity of a senior creative director — then closes the loop with real CTR data, competitor gap analysis, brand voice compliance, localisation readiness, and Slack-ready summaries.

---

## Features

| # | Feature | What it does |
|---|---------|--------------|
| 1 | **8-Dimension Critique** | Clarity, Audience Fit, CTA Strength, Value Proposition, Emotional Hook, Platform Fit, Credibility, Brevity — each scored 1-10 with a concrete fix |
| 2 | **Performance Feedback Loop** | Record real CTR/ROAS/conversion data against past critiques. Identify which dimensions actually predict performance for your category |
| 3 | **Competitor Gap Analysis** | Pass 1-4 competitor ads, get a per-dimension gap table, differentiation score, category clichés, and unique angles nobody owns |
| 4 | **Brand Voice Compliance** | Upload a voice profile (prohibited words, tone, persona, examples). Rule-based scan + LLM tone assessment flags every violation with field, text, and suggested fix |
| 5 | **Localisation Readiness** | Check copy before translating: idioms, CTA norms, currency/regulatory risks, translation difficulty score, and locale-specific rewrites |
| 6 | **Slack Summary** | Every critique includes a pre-formatted `slack_summary` field ready to post to your #ad-review channel |

---

## Quick Start (Docker)

```bash
cp .env.example .env          # add your ANTHROPIC_API_KEY
docker-compose up api         # start the REST API on :8000
curl -s http://localhost:8000/health
```

---

## CLI Usage

```bash
pip install -r requirements.txt

# Critique a single ad (from JSON file)
python main.py critique --file examples/sample_fintech_ad.json

# Critique inline
python main.py critique \
  --headline "Finally, Sunscreen That Doesn't Feel Like Sunscreen" \
  --platform facebook --audience "Women 25-40" \
  --goal conversion --category "D2C skincare"

# Batch critique a directory of ads
python main.py critique --batch ./examples/ --format json

# Output formats: markdown (default), json, html
python main.py critique --file examples/sample_fintech_ad.json --format html --output report.html
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/dimensions` | List 8 scoring dimensions with weights |
| `POST` | `/critique` | Critique a single ad |
| `POST` | `/critique/batch` | Critique multiple ads, get fleet summary |
| `POST` | `/competitors` | Competitor gap analysis |
| `POST` | `/brand-voice` | Brand voice compliance check |
| `POST` | `/localise` | Localisation readiness check |
| `POST` | `/benchmark` | Trend benchmarking (rule-based, no LLM) |
| `POST` | `/feedback` | Record real performance metrics |
| `GET` | `/feedback/insights` | Dimension insights from feedback data |

---

## Sample Output

```json
{
  "overall_score": 72,
  "overall_verdict": "strong",
  "executive_summary": "Strong positioning — the 'doesn't feel like sunscreen' hook is genuinely differentiated...",
  "dimensions": [
    { "dimension": "Value Proposition", "score": 8, "verdict": "USP is specific and ownable." },
    { "dimension": "CTA Strength", "score": 6, "verdict": "...", "issue": "Generic 'Shop Now'", "fix": "Add urgency or benefit" }
  ],
  "variants": [
    { "label": "Variant A", "headline": "SPF 50 That Disappears. For Real.", "cta": "Try It Risk-Free", "rationale": "Leads with the proof, not the promise." }
  ],
  "slack_summary": ":white_check_mark: *[STRONG] 72/100 — Finally, Sunscreen That Doesn't Feel...*\n> Strong positioning...\n:warning: Top issue: Generic CTA\n:white_check_mark: Top strength: Specific, ownable USP\n:bulb: Best variant: \"SPF 50 That Disappears. For Real.\" — Leads with proof."
}
```

---

## Output Schema

```json
{
  "overall_score": "1-100",
  "overall_verdict": "strong | needs_work | weak | do_not_run",
  "executive_summary": "string",
  "dimensions": [{ "dimension": "string", "score": "1-10", "verdict": "string", "issue": "string|null", "fix": "string|null" }],
  "critical_issues": ["string"],
  "minor_issues": ["string"],
  "strengths": ["string"],
  "variants": [{ "label": "string", "headline": "string", "body": "string|null", "cta": "string|null", "rationale": "string" }],
  "ab_test_recommendation": "string",
  "platform_fit_note": "string",
  "slack_summary": "string"
}
```

---

## Running Tests

```bash
pip install -r requirements.txt
pytest
# 68 tests, 0 failures
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | **Required.** Your Anthropic API key. |
| `MODEL` | `claude-sonnet-4-6` | Claude model to use. |
| `MAX_TOKENS` | `2048` | Max tokens per critique. |
| `FEEDBACK_STORE_PATH` | — | Optional path to persist feedback as JSON (e.g. `./feedback_store.json`). |
| `LOG_LEVEL` | `INFO` | Logging verbosity. |

---

## Live Demo

[swapnanil.github.io/ad-copy-critic](https://swapnanil.github.io/ad-copy-critic)

---

Built by **Swapnanil Saha** — [swapnanilsaha.com](https://swapnanilsaha.com)
