from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import time
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "llm_requests_total",
    "Total LLM requests",
    ["model", "status"]
)
REQUEST_DURATION = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration",
    ["model"]
)

app = FastAPI(
    title="Ollama MLOps API",
    description="FastAPI wrapper for Ollama LLM — MLOps Portfolio Project",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://ollama-service:11434"

class PromptRequest(BaseModel):
    prompt: str
    model: str = "phi3:mini"
    stream: bool = False

class HealthResponse(BaseModel):
    status: str
    ollama_reachable: bool
    available_models: list

@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            models = [m["name"] for m in response.json().get("models", [])]
            return {"status": "ok", "ollama_reachable": True, "available_models": models}
    except Exception as e:
        logger.error(f"Ollama unreachable: {e}")
        return {"status": "degraded", "ollama_reachable": False, "available_models": []}

@app.post("/generate")
async def generate(request: PromptRequest):
    start_time = time.time()
    logger.info(f"Request: model={request.model}, prompt_len={len(request.prompt)}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "stream": request.stream
                }
            )
            response.raise_for_status()
            data = response.json()

        duration = time.time() - start_time
        REQUEST_COUNT.labels(model=request.model, status="success").inc()
        REQUEST_DURATION.labels(model=request.model).observe(duration)

        logger.info(f"Response: duration={duration:.2f}s, tokens={data.get('eval_count', 0)}")

        return {
            "model": request.model,
            "response": data["response"],
            "duration_seconds": round(duration, 2),
            "tokens_generated": data.get("eval_count", 0)
        }

    except Exception as e:
        REQUEST_COUNT.labels(model=request.model, status="error").inc()
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    return {
        "service": "Ollama MLOps API",
        "docs": "/docs",
        "health": "/health",
        "generate": "/generate"
    }
