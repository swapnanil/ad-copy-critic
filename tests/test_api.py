"""Tests for the FastAPI endpoints."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)

VALID_AD = {
    "headline": "Finally, Sunscreen That Doesn't Feel Like Sunscreen",
    "body": "Ultra-light SPF 50 that disappears into skin in seconds.",
    "cta": "Shop Now — Free Shipping Over $40",
    "platform": "facebook",
    "target_audience": "Women 25-40 interested in skincare",
    "campaign_goal": "conversion",
    "product_category": "D2C skincare",
    "usp": "Invisible finish, SPF 50, reef-safe",
}

MOCK_CRITIQUE = {
    "overall_score": 72,
    "overall_verdict": "strong",
    "executive_summary": "Strong ad with clear value proposition.",
    "dimensions": [
        {"dimension": "Clarity", "score": 8, "verdict": "Clear.", "issue": None, "fix": None},
        {"dimension": "Audience Fit", "score": 7, "verdict": "Well targeted.", "issue": None, "fix": None},
        {"dimension": "CTA Strength", "score": 7, "verdict": "Good CTA.", "issue": None, "fix": None},
        {"dimension": "Value Proposition", "score": 8, "verdict": "Strong.", "issue": None, "fix": None},
        {"dimension": "Emotional Hook", "score": 7, "verdict": "Engaging.", "issue": None, "fix": None},
        {"dimension": "Platform Fit", "score": 7, "verdict": "Appropriate.", "issue": None, "fix": None},
        {"dimension": "Credibility", "score": 6, "verdict": "Acceptable.", "issue": None, "fix": None},
        {"dimension": "Brevity", "score": 6, "verdict": "Slightly long.", "issue": None, "fix": None},
    ],
    "critical_issues": [],
    "minor_issues": ["Body slightly long."],
    "strengths": ["Strong hook.", "Clear value prop."],
    "variants": [
        {"label": "Variant A", "headline": "Better Headline", "body": "Better body.", "cta": "Buy Now", "rationale": "More direct."},
        {"label": "Variant B", "headline": "Alternative Headline", "body": "Alternative body.", "cta": "Try Free", "rationale": "Social proof."},
    ],
    "ab_test_recommendation": "Run Variant A vs control.",
    "platform_fit_note": "Good platform fit.",
}


def _mock_critique_ad(ad_input):
    from agent.models import AdCritique
    return AdCritique(**MOCK_CRITIQUE)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model" in data


def test_dimensions():
    response = client.get("/dimensions")
    assert response.status_code == 200
    data = response.json()
    assert "dimensions" in data
    assert len(data["dimensions"]) == 8
    names = [d["name"] for d in data["dimensions"]]
    assert "Clarity" in names
    assert "Value Proposition" in names


@patch("agent.critic._get_client")
def test_critique_endpoint_valid(mock_get_client):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(MOCK_CRITIQUE))]
    mock_client.messages.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    response = client.post("/critique", json=VALID_AD)
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert 1 <= data["overall_score"] <= 100
    assert "variants" in data
    assert 2 <= len(data["variants"]) <= 3


def test_critique_endpoint_invalid_input():
    response = client.post("/critique", json={"headline": "Missing required fields"})
    assert response.status_code == 422


def test_critique_endpoint_invalid_platform():
    bad_ad = {**VALID_AD, "platform": "tiktok"}
    response = client.post("/critique", json=bad_ad)
    assert response.status_code == 422


@patch("agent.critic._get_client")
def test_critique_batch_endpoint(mock_get_client):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(MOCK_CRITIQUE))]
    mock_client.messages.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    second_ad = {
        **VALID_AD,
        "headline": "Second Ad Headline",
        "platform": "linkedin",
        "campaign_goal": "lead_generation",
    }
    response = client.post("/critique/batch", json={"ads": [VALID_AD, second_ad]})
    assert response.status_code == 200
    data = response.json()
    assert "critiques" in data
    assert len(data["critiques"]) == 2
    assert "fleet_summary" in data
    assert "average_score" in data
    assert "weakest_dimension" in data


def test_critique_batch_endpoint_empty():
    response = client.post("/critique/batch", json={"ads": []})
    assert response.status_code == 422
