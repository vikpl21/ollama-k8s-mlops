#!/bin/bash
set -e

echo "Starting MLflow server..."

exec mlflow server \
  --host 0.0.0.0 \
  --port 8080 \
  --backend-store-uri "${MLFLOW_BACKEND_URI}" \
  --default-artifact-root "${MLFLOW_ARTIFACT_ROOT}" \
  --allowed-hosts "*"
