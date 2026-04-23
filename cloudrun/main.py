from fastapi import FastAPI
from pydantic import BaseModel
import os
import httpx
import asyncio

app = FastAPI(
    title="Ollama MLOps API — Cloud Run",
    description="FastAPI on GCP Cloud Run — MLOps Portfolio",
    version="1.0.0"
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "")

class PromptRequest(BaseModel):
    prompt: str
    model: str = "phi3:mini"

@app.get("/")
async def root():
    return {
        "service": "Ollama MLOps API",
        "platform": "GCP Cloud Run",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "platform": "GCP Cloud Run",
        "region": os.getenv("K_SERVICE", "local"),
        "ollama_configured": bool(OLLAMA_URL),
    }

@app.post("/generate")
async def generate(request: PromptRequest):
    if not OLLAMA_URL:
        # Demo mode — Cloud Run без локального Ollama
        return {
            "model": request.model,
            "prompt": request.prompt,
            "response": (
                f"[Cloud Run Demo Mode] This API is running on GCP Cloud Run. "
                f"In production, connect OLLAMA_URL env var to a running Ollama instance. "
                f"Your prompt was: '{request.prompt}'"
            ),
            "platform": "GCP Cloud Run",
            "mode": "demo",
        }
    # Production mode — якщо є реальний Ollama endpoint
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": request.model, "prompt": request.prompt, "stream": False}
        )
        data = response.json()
        return {"model": request.model, "response": data["response"], "platform": "GCP Cloud Run"}

@app.get("/info")
async def info():
    return {
        "deployment": "GCP Cloud Run",
        "project": "ollama-mlops",
        "stack": ["Python", "FastAPI", "Docker", "GCP Cloud Run", "Artifact Registry"],
        "github": "https://github.com/vikpl21/ollama-k8s-mlops",
    }
