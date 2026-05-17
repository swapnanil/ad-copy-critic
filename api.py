"""Ad Copy Critic — FastAPI REST API."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="Ad Copy Critic",
    description="Evaluate ad copy with the precision of a senior creative strategist.",
    version="1.0.0",
)

MODEL = os.getenv("MODEL", "claude-sonnet-4-6")

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


class BatchCritiqueRequest(BaseModel):
    ads: list


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": MODEL}


@app.get("/dimensions")
def dimensions() -> dict:
    return {
        "dimensions": [
            {
                "name": name,
                "weight": weight,
                "weight_pct": f"{int(weight * 100)}%",
            }
            for name, weight in DIMENSION_WEIGHTS.items()
        ]
    }


@app.post("/critique")
def critique_endpoint(ad_input: dict) -> dict:
    from agent import AdCopyInput, critique_ad

    try:
        parsed = AdCopyInput(**ad_input)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = critique_ad(parsed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Critique failed: {e}")

    return result.model_dump()


@app.post("/critique/batch")
def critique_batch_endpoint(request: BatchCritiqueRequest) -> dict:
    from agent import AdCopyInput, critique_batch

    if not request.ads:
        raise HTTPException(status_code=422, detail="No ads provided.")

    parsed_ads = []
    errors = []
    for i, ad in enumerate(request.ads):
        try:
            parsed_ads.append(AdCopyInput(**ad))
        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    if not parsed_ads:
        raise HTTPException(status_code=422, detail={"message": "No valid ads.", "errors": errors})

    try:
        result = critique_batch(parsed_ads)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch critique failed: {e}")

    response = result.model_dump()
    if errors:
        response["parse_errors"] = errors

    return response
