import os
"""
Material Classification Experiment with MLflow Tracking
"""
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment("material-classification")

np.random.seed(42)
n_samples = 1000

def generate_material_data():
    materials = {
        "metal":   {"texture": (0.1, 0.05), "reflect": (0.9, 0.05), "weight": (0.8, 0.1),  "hard": (0.9, 0.05), "conduct": (0.95, 0.03)},
        "plastic": {"texture": (0.5, 0.1),  "reflect": (0.4, 0.1),  "weight": (0.2, 0.05), "hard": (0.3, 0.1),  "conduct": (0.05, 0.02)},
        "wood":    {"texture": (0.8, 0.1),  "reflect": (0.2, 0.05), "weight": (0.4, 0.1),  "hard": (0.5, 0.1),  "conduct": (0.1,  0.03)},
        "glass":   {"texture": (0.05,0.02), "reflect": (0.85,0.05), "weight": (0.5, 0.08), "hard": (0.7, 0.05), "conduct": (0.3,  0.05)},
        "fabric":  {"texture": (0.95,0.03), "reflect": (0.1, 0.05), "weight": (0.05,0.02), "hard": (0.05,0.02), "conduct": (0.02, 0.01)},
    }
    X, y = [], []
    per_class = n_samples // len(materials)
    for label, (mat_name, props) in enumerate(materials.items()):
        for _ in range(per_class):
            row = [
                np.clip(np.random.normal(props["texture"][0], props["texture"][1]), 0, 1),
                np.clip(np.random.normal(props["reflect"][0], props["reflect"][1]), 0, 1),
                np.clip(np.random.normal(props["weight"][0],  props["weight"][1]),  0, 1),
                np.clip(np.random.normal(props["hard"][0],    props["hard"][1]),    0, 1),
                np.clip(np.random.normal(props["conduct"][0], props["conduct"][1]), 0, 1),
            ]
            X.append(row)
            y.append(label)
    return np.array(X), np.array(y), list(materials.keys())

X, y, class_names = generate_material_data()
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

print(f"Dataset: {len(X_train)} train, {len(X_test)} test samples")
print(f"Classes: {class_names}\n")

experiments = [
    {
        "name": "RandomForest-100",
        "model": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
        "params": {"n_estimators": 100, "max_depth": 10, "model_type": "RandomForest"},
        "scaled": False,
    },
    {
        "name": "RandomForest-200",
        "model": RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42),
        "params": {"n_estimators": 200, "max_depth": 20, "model_type": "RandomForest"},
        "scaled": False,
    },
    {
        "name": "SVM-C1",
        "model": SVC(kernel="rbf", C=1.0, random_state=42),
        "params": {"kernel": "rbf", "C": 1.0, "model_type": "SVM"},
        "scaled": True,
    },
    {
        "name": "SVM-C10",
        "model": SVC(kernel="rbf", C=10.0, random_state=42),
        "params": {"kernel": "rbf", "C": 10.0, "model_type": "SVM"},
        "scaled": True,
    },
    {
        "name": "LogisticRegression",
        "model": LogisticRegression(C=1.0, max_iter=1000, random_state=42),
        "params": {"C": 1.0, "max_iter": 1000, "model_type": "LogisticRegression"},
        "scaled": True,
    },
]

results = []

for exp in experiments:
    with mlflow.start_run(run_name=exp["name"]):
        mlflow.log_params(exp["params"])
        mlflow.log_param("n_classes",      len(class_names))
        mlflow.log_param("n_features",     X.shape[1])
        mlflow.log_param("train_size",     len(X_train))
        mlflow.log_param("feature_scaling",exp["scaled"])

        X_tr = X_train_scaled if exp["scaled"] else X_train
        X_te = X_test_scaled  if exp["scaled"] else X_test
        exp["model"].fit(X_tr, y_train)
        y_pred = exp["model"].predict(X_te)

        acc  = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average="weighted")
        rec  = recall_score(y_test, y_pred, average="weighted")
        f1   = f1_score(y_test, y_pred, average="weighted")

        mlflow.log_metric("accuracy",  acc)
        mlflow.log_metric("precision", prec)
        mlflow.log_metric("recall",    rec)
        mlflow.log_metric("f1_score",  f1)

        # MLflow 3.x compatible model logging
        mlflow.sklearn.log_model(exp["model"], artifact_path="model")

        # Feature importance artifact
        if hasattr(exp["model"], "feature_importances_"):
            feature_names = ["texture","reflectivity","weight","hardness","conductivity"]
            importance_df = pd.DataFrame({
                "feature":    feature_names,
                "importance": exp["model"].feature_importances_
            }).sort_values("importance", ascending=False)
            importance_df.to_csv("/tmp/feature_importance.csv", index=False)
            mlflow.log_artifact("/tmp/feature_importance.csv")

        results.append({"name": exp["name"], "accuracy": acc, "f1_score": f1})
        print(f"✅ {exp['name']:22s} | acc={acc:.4f} | f1={f1:.4f}")

print(f"\n{'='*55}")
print("EXPERIMENT SUMMARY")
print(f"{'='*55}")
best = max(results, key=lambda x: x["f1_score"])
for r in sorted(results, key=lambda x: x["f1_score"], reverse=True):
    marker = " ← BEST" if r["name"] == best["name"] else ""
    print(f"{r['name']:22s} | f1={r['f1_score']:.4f}{marker}")
print(f"\nView results: http://localhost:5000")
