"""
MLflow Model Serving — завантажує найкращу модель з MLflow Registry
"""
import mlflow
import mlflow.sklearn
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

MLFLOW_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://localhost:5000"
)

# Назви класів матеріалів
MATERIAL_CLASSES = ["metal", "plastic", "wood", "glass", "fabric"]

class MaterialClassifier:
    def __init__(self):
        self.model = None
        self.model_name = "material-classifier"
        self._load_model()

    def _load_model(self):
        try:
            mlflow.set_tracking_uri(MLFLOW_URI)
            client = mlflow.MlflowClient()

            # Шукаємо найкращий run по F1
            runs = client.search_runs(
                experiment_ids=["1"],
                order_by=["metrics.f1_score DESC"],
                max_results=1
            )

            if not runs:
                logger.warning("No runs found in MLflow")
                return

            best_run = runs[0]
            run_id = best_run.info.run_id
            f1 = best_run.data.metrics.get("f1_score", 0)

            logger.info(f"Loading model from run {run_id} (F1={f1:.4f})")

            # Завантажуємо модель
            self.model = mlflow.sklearn.load_model(
                f"runs:/{run_id}/model"
            )
            self.run_id = run_id
            self.f1_score = f1
            logger.info("Model loaded successfully!")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def predict(self, features: list) -> dict:
        if self.model is None:
            return {"error": "Model not loaded"}

        arr = np.array(features).reshape(1, -1)
        prediction = self.model.predict(arr)[0]
        
        # Отримай probability якщо є
        proba = None
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(arr)[0].tolist()

        return {
            "material": MATERIAL_CLASSES[prediction],
            "class_id": int(prediction),
            "confidence": round(max(proba), 4) if proba else None,
            "probabilities": {
                MATERIAL_CLASSES[i]: round(p, 4)
                for i, p in enumerate(proba)
            } if proba else None,
            "model_run_id": self.run_id,
            "model_f1_score": self.f1_score,
        }

# Singleton
_classifier = None

def get_classifier() -> MaterialClassifier:
    global _classifier
    if _classifier is None:
        _classifier = MaterialClassifier()
    return _classifier
