from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Ollama MLOps API"
    assert "docs" in data
    assert "health" in data

def test_health_ollama_unreachable():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ollama_reachable" in data
    assert "available_models" in data

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"llm_requests_total" in response.content

def test_generate_missing_prompt():
    response = client.post(
        "/generate",
        json={"model": "phi3:mini"}
    )
    assert response.status_code == 422

def test_generate_invalid_json():
    response = client.post(
        "/generate",
        content="not json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
