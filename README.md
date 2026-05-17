# ad-copy-critic
> Eight dimensions. One score. Rewrites included. Stop guessing whether your ad copy works.

Part of the [llm-tools suite](https://github.com/swapnanil) by [Swapnanil Saha](https://swapnanilsaha.com)

## What it does

Copywriters spend hours revising headlines that feel wrong but nobody can articulate why. Ad Copy Critic gives every ad a structured critique across eight weighted dimensions — each scored with evidence and a specific fix — plus 2–3 rewrite variants with rationale for every change made.

## Quick start

```bash
git clone https://github.com/swapnanil/ad-copy-critic
cd ad-copy-critic
cp .env.example .env   # add your ANTHROPIC_API_KEY
docker-compose up api
```

## CLI usage

```bash
# Critique a single ad
docker-compose run cli critique \
  --file examples/sample_fintech_ad.json \
  --format markdown

# Batch critique a folder of ads
docker-compose run cli batch \
  --dir examples/ads/ \
  --platform linkedin \
  --format html --output reports/

# Interactive mode
docker-compose run --rm -it cli critique --interactive
```

## API usage

```bash
# Critique an ad
curl -X POST http://localhost:8000/critique \
  -H "Content-Type: application/json" \
  -d '{"headline": "Manage Your Business Expenses Better", "cta": "Learn More", "platform": "linkedin", "target_audience": "CFOs at mid-size B2B companies", "campaign_goal": "lead_generation"}'

# Batch critique
curl -X POST http://localhost:8000/batch \
  -F "file=@examples/ads/q2_batch.json" \
  -F "platform=linkedin"
```

## Input / Output

**Input:**
```json
{
  "headline": "Manage Your Business Expenses Better",
  "cta": "Learn More",
  "platform": "linkedin",
  "target_audience": "CFOs at mid-size B2B companies",
  "campaign_goal": "lead_generation"
}
```

**Output excerpt:**
```json
{
  "overall_score": 28,
  "verdict": "needs_work",
  "dimensions": {
    "cta": {
      "score": 3,
      "issue": "'Learn More' signals passive intent — wrong for CFO lead-gen",
      "fix": "Replace with 'See How Much You're Overspending'"
    }
  },
  "rewrite_variants": [
    {
      "headline": "Cut Finance Team Reporting Time by 47%",
      "rationale": "Specificity + urgency added; CFO-relevant metric anchors the claim"
    }
  ]
}
```

## Built with

- Python 3.11
- Anthropic SDK (claude-sonnet-4-6)
- FastAPI + uvicorn
- Docker + docker-compose
- pytest

## Author

Swapnanil Saha · [swapnanilsaha.com](https://swapnanilsaha.com) · [LinkedIn](https://linkedin.com/in/swapnanil)
