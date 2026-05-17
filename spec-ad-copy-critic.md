# Spec: Ad Copy Critic
**Tool 1 of 5 — llm-tools suite by Swapnanil Saha**

---

## Overview

A production-grade Python CLI + REST API that evaluates ad copy with the precision of a senior creative strategist and the rigor of a performance marketer. Input any ad copy along with campaign context (target audience, platform, goal, product category) and receive a structured critique: dimension-by-dimension scoring, identified weaknesses with root causes, rewritten variants, and A/B test recommendations.

Built with the Anthropic Python SDK. Fully containerised with Docker. Designed for performance marketers, creative teams, and agencies who need fast, expert-level feedback on ad copy before spend goes live.

---

## Business Problem This Solves

Bad ad copy is expensive. A headline that doesn't resonate with the target audience, a CTA that's too weak, or copy that doesn't match the platform's native tone can tank CTR and inflate CPA before anyone notices. Creative review is slow, subjective, and often skips the performance lens entirely. This tool encodes 9 years of ad-tech performance knowledge into an instant, structured critique that bridges creative quality and business outcomes.

---

## Tech Stack

- **Language**: Python 3.11+
- **LLM**: Anthropic SDK — model: `claude-sonnet-4-6`
- **API Framework**: FastAPI with uvicorn
- **CLI**: Typer
- **Output formats**: Markdown report, JSON, HTML scorecard
- **Containerisation**: Docker + docker-compose
- **Testing**: pytest
- **Env management**: python-dotenv

---

## Project Structure

```
ad-copy-critic/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
├── main.py                    # CLI entry point
├── api.py                     # FastAPI app
├── agent/
│   ├── __init__.py
│   ├── critic.py              # Core critique logic
│   ├── prompts.py             # System + user prompts
│   └── models.py              # Pydantic input/output models
├── examples/
│   ├── sample_fintech_ad.json
│   ├── sample_ecommerce_ad.json
│   ├── sample_saas_ad.json
│   └── sample_output.json
└── tests/
    ├── test_critic.py
    └── test_api.py
```

---

## Input Schema (`agent/models.py`)

```python
class AdCopyInput(BaseModel):
    # The copy itself
    headline: str                        # primary headline
    body: str | None                     # body copy (optional for display ads)
    cta: str | None                      # call to action text
    tagline: str | None                  # optional tagline

    # Campaign context
    platform: Literal[
        "google_search", "google_display", "facebook", "instagram",
        "linkedin", "native", "programmatic_display", "email", "other"
    ]
    target_audience: str                 # e.g. "CFOs at mid-size B2B SaaS companies"
    campaign_goal: Literal[
        "awareness", "consideration", "lead_generation",
        "conversion", "retention", "app_install"
    ]
    product_category: str                # e.g. "project management SaaS", "D2C skincare"
    usp: str | None                      # unique selling proposition if known
    competitor_copy: str | None          # optional competitor ad for comparison
    character_limits: dict | None        # e.g. {"headline": 30, "body": 90}
```

---

## Output Schema (`agent/models.py`)

```python
class DimensionScore(BaseModel):
    dimension: str                       # e.g. "Clarity", "CTA Strength"
    score: int                           # 1–10
    verdict: str                         # one sentence assessment
    issue: str | None                    # specific problem if score < 7
    fix: str | None                      # specific fix if score < 7

class AdVariant(BaseModel):
    label: str                           # e.g. "Variant A — Urgency-led"
    headline: str
    body: str | None
    cta: str | None
    rationale: str                       # why this variant addresses the weaknesses

class AdCritique(BaseModel):
    overall_score: int                   # 1–100 weighted composite
    overall_verdict: Literal[
        "strong", "needs_work", "weak", "do_not_run"
    ]
    executive_summary: str              # 2–3 sentences, non-technical
    
    # Dimension breakdown
    dimensions: list[DimensionScore]    # see dimensions below
    
    # Top issues
    critical_issues: list[str]          # must fix before running
    minor_issues: list[str]             # nice to fix
    
    # What's working
    strengths: list[str]
    
    # Rewrites
    variants: list[AdVariant]           # 2–3 improved variants
    
    # Strategic note
    ab_test_recommendation: str         # which variant to test first and why
    platform_fit_note: str              # specific note on platform suitability
```

---

## Scoring Dimensions

The critique evaluates 8 dimensions, each scored 1–10:

```
1. Clarity           — Is the message immediately understood in <3 seconds?
2. Audience Fit      — Does the language, tone, and pain point match the target audience?
3. CTA Strength      — Is the call-to-action specific, compelling, and low-friction?
4. Value Proposition — Is the USP clear and differentiated from generic claims?
5. Emotional Hook    — Does it create desire, urgency, fear of missing out, or curiosity?
6. Platform Fit      — Does the copy match the native tone and format of the platform?
7. Credibility       — Are claims specific and believable, or vague and generic?
8. Brevity           — Does it respect attention span and character constraints?
```

**Weighted composite score:**
```
Clarity: 15%
Audience Fit: 15%
CTA Strength: 15%
Value Proposition: 20%
Emotional Hook: 10%
Platform Fit: 10%
Credibility: 10%
Brevity: 5%
```

---

## System Prompt (`agent/prompts.py`)

```
You are a senior creative strategist and performance marketing expert with deep experience
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

Respond ONLY with valid JSON matching the output schema. No preamble, no markdown fences.
```

---

## CLI Interface

```bash
# From JSON file
python main.py critique --file examples/sample_fintech_ad.json

# Quick inline mode
python main.py critique \
  --headline "Get More Done With Less" \
  --cta "Start Free Trial" \
  --platform linkedin \
  --audience "Product managers at Series B startups" \
  --goal lead_generation \
  --category "project management SaaS"

# With competitor copy for comparison
python main.py critique --file ad.json --competitor "Try the tool 10,000 teams trust"

# Output formats
python main.py critique --file ad.json --format markdown
python main.py critique --file ad.json --format json
python main.py critique --file ad.json --format html --output report.html

# Batch mode — critique multiple ads from a folder
python main.py critique --batch examples/ --format markdown --output batch_report.md
```

---

## API Endpoints

```
POST /critique
  Body: AdCopyInput JSON
  Returns: AdCritique

POST /critique/batch
  Body: list[AdCopyInput]
  Returns: list[AdCritique] + fleet summary

GET /health
  Returns: { "status": "ok", "model": "claude-sonnet-4-6" }

GET /dimensions
  Returns: scoring dimension definitions + weights
```

---

## Docker Setup

**Dockerfile:**
- Base: `python:3.11-slim`
- Non-root user
- Expose port 8000

**docker-compose.yml:**
```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./examples:/app/examples
      - ./reports:/app/reports

  cli:
    build: .
    env_file: .env
    volumes:
      - ./examples:/app/examples
      - ./reports:/app/reports
    entrypoint: ["python", "main.py"]
    profiles: ["cli"]
```

**Run API:**
```bash
docker-compose up api
```

**Run CLI:**
```bash
docker-compose run cli critique --file examples/sample_fintech_ad.json
```

---

## .env.example

```
ANTHROPIC_API_KEY=sk-ant-...
MODEL=claude-sonnet-4-6
MAX_TOKENS=2048
LOG_LEVEL=INFO
```

---

## Sample Input Files to Generate

**sample_fintech_ad.json:**
LinkedIn lead gen ad for a B2B expense management SaaS. Headline: "Manage Your Business Expenses Better". Body: "Our platform helps finance teams track spending and save money. Trusted by companies worldwide." CTA: "Learn More". Target: CFOs and finance directors at SMBs. Deliberately weak — generic headline, vague body, weak CTA, no specificity. Tool should score this 28/100 and rewrite it significantly.

**sample_ecommerce_ad.json:**
Facebook conversion ad for a D2C skincare brand. Headline: "Finally, Skincare That Actually Works". Body: "Dermatologist-tested formula with 97% of users seeing results in 14 days. No parabens, no compromise." CTA: "Shop Now — Free Shipping Over ₹999". Target: Women 25–40 interested in clean beauty. Deliberately strong — specific claims, social proof, urgency. Tool should score 78/100 with minor improvements.

**sample_saas_ad.json:**
Google Search ad for a project management tool. Headline: "Best Project Management Tool". Body: "Award-winning software for teams. Start your free trial today." CTA: "Get Started". No keywords in headline. Superlative without proof. Tool should flag quality score risk, score 35/100.

---

## Error Handling

- Empty headline → reject with helpful message
- Copy exceeds character limits if provided → flag in critique, do not reject
- Platform = "other" → apply general digital advertising standards
- LLM returns invalid JSON → retry once with schema correction prompt
- API rate limit → exponential backoff, 3 retries

---

## README Must Include

- Business problem (one paragraph)
- The 8 scoring dimensions with weights
- Quick start with Docker
- CLI usage with examples
- API usage with curl examples
- Sample input → sample output (show a before/after rewrite)
- Built by: Swapnanil Saha — link to swapnanilsaha.com

---

## Tests

- `test_critic.py`: test all 3 sample inputs with mocked Anthropic responses
- `test_api.py`: test /critique and /critique/batch endpoints
- Assert overall_score is always 1–100
- Assert variants always contains 2–3 items
- Assert do_not_run verdict only appears when overall_score < 25
- Assert character limit violations are always flagged when limits provided
