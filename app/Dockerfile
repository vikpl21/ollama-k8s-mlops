FROM python:3.11-slim
WORKDIR /app
# Install dependencies first (Docker cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 5 -r requirements.txt
# Copy app
COPY main.py .
COPY model_serving.py .
# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python3 -c "import httpx; httpx.get('http://localhost:8000/health')"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
