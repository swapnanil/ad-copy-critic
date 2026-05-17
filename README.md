# Ad Copy Critic

Evaluate ad copy with the precision of a senior creative strategist. Get dimension-by-dimension scores, actionable fixes, rewritten variants, and A/B test recommendations — in seconds.

Built by [Swapnanil Saha](https://swapnanilsaha.com) · Tool 1 of 5 in the **llm-tools** suite · Powered by Claude (Anthropic)

---

## The Business Problem

Most ad creative feedback is vague ("make it punchier"), delayed (waiting for agency review), or absent entirely (ship and hope). Ad Copy Critic applies structured performance-marketing judgment to every piece of copy before it goes live — catching generic CTAs, platform mismatches, credibility risks, and character limit violations that silently kill campaign ROI.

---

## Scoring Dimensions

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Value Proposition | 20% | Is the core differentiator explicit and compelling? |
| Clarity | 15% | Can a stranger understand the offer in 3 seconds? |
| Audience Fit | 15% | Does the language match the target persona's mindset? |
| CTA Strength | 15% | Does the call to action drive the intended action? |
| Emotional Hook | 10% | Does the copy trigger an emotion relevant to purchase? |
| Platform Fit | 10% | Is the format/length/tone right for this channel? |
| Credibility | 10% | Are claims believable and backed by proof? |
| Brevity | 5% | Is every word earning its place? |

**Score interpretation:**
- 70–100: Strong — ready to run
- 40–69: Needs Work — revise before launch
- 25–39: Weak — significant rework required
- 1–24: Do Not Run — fundamental issues

---

## Quickstart (Docker)

```bash
# Clone and configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Start the API
docker compose up api

# Run a critique via curl
curl -s -X POST http://localhost:8000/critique \
  -H "Content-Type: application/json" \
  -d @examples/sample_ecommerce_ad.json | jq .
```

---

## CLI Usage

```bash
pip install -r requirements.txt
cp .env.example .env  # set ANTHROPIC_API_KEY

# Critique from a JSON file (markdown output)
python main.py --file examples/sample_ecommerce_ad.json

# Inline mode
python main.py \
  --headline "Finally, Sunscreen That Doesn't Feel Like Sunscreen" \
  --platform facebook \
  --audience "Women 25-40, skincare-interested" \
  --goal conversion \
  --category "D2C skincare" \
  --usp "Invisible finish, SPF 50, reef-safe"

# Output as JSON
python main.py --file examples/sample_fintech_ad.json --format json

# Save HTML scorecard
python main.py --file examples/sample_ecommerce_ad.json --format html --output reports/ecommerce.html

# Batch mode (critique all JSON files in a directory)
python main.py --batch examples/
```

---

## API Usage

### Start the server

```bash
uvicorn api:app --reload
```

### Endpoints

**`GET /health`**
```bash
curl http://localhost:8000/health
# {"status":"ok","model":"claude-sonnet-4-6"}
```

**`GET /dimensions`**
```bash
curl http://localhost:8000/dimensions
```

**`POST /critique`**
```bash
curl -s -X POST http://localhost:8000/critique \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Finally, Sunscreen That Doesn'\''t Feel Like Sunscreen",
    "body": "Ultra-light SPF 50 that disappears into skin in seconds. No white cast.",
    "cta": "Shop Now — Free Shipping Over $40",
    "platform": "facebook",
    "target_audience": "Women 25-40 interested in skincare",
    "campaign_goal": "conversion",
    "product_category": "D2C skincare",
    "usp": "Invisible finish, SPF 50, reef-safe"
  }' | jq .
```

**`POST /critique/batch`**
```bash
curl -s -X POST http://localhost:8000/critique/batch \
  -H "Content-Type: application/json" \
  -d '{"ads": [...]}' | jq .
```

---

## Sample Before / After

**Original (LinkedIn B2B fintech — score: ~28/100)**
> Headline: "Grow Your Business with Our Financial Solutions"
> CTA: "Learn More"

**Critique flags:** Generic headline could describe any bank. "Learn More" CTA scores max 3/10 — gives no indication of what happens next. No keyword in headline creates brand safety risk on LinkedIn Matched Audiences.

**Variant A (AI-generated):**
> Headline: "Working Capital Approved in 24 Hours — No Collateral"
> CTA: "Check Your Eligibility → 2 Minutes"

**Variant B (AI-generated):**
> Headline: "CFOs Use This to Bridge Cash Flow Gaps Without Dilution"
> CTA: "See How It Works"

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Input Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `headline` | string | Yes | Main ad headline |
| `body` | string | No | Ad body copy |
| `cta` | string | No | Call to action text |
| `tagline` | string | No | Optional tagline |
| `platform` | enum | Yes | `google_search`, `google_display`, `facebook`, `instagram`, `linkedin`, `native`, `programmatic_display`, `email`, `other` |
| `target_audience` | string | Yes | Description of target audience |
| `campaign_goal` | enum | Yes | `awareness`, `consideration`, `lead_generation`, `conversion`, `retention`, `app_install` |
| `product_category` | string | Yes | Product/service category |
| `usp` | string | No | Unique selling proposition |
| `competitor_copy` | string | No | Competitor ad for comparison |
| `character_limits` | dict | No | e.g. `{"headline": 30, "body": 90}` |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Required. Your Anthropic API key. |
| `MODEL` | `claude-sonnet-4-6` | Claude model to use. |
| `MAX_TOKENS` | `2048` | Max tokens for API response. |
| `LOG_LEVEL` | `INFO` | Logging verbosity. |
