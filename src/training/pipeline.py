import os
import io
import json
from pathlib import Path

import boto3
import joblib
import pandas as pd

from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, recall_score, make_scorer
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[2]))

from src.evaluation.registry import promote_if_approved

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

BUCKET = os.environ.get("BUCKET", "<your-bucket>")
REGION = "eu-north-1"
PROCESSED_PREFIX = "data/processed/"
MINIMUM_RECALL = 0.90

s3 = boto3.client("s3", region_name=REGION)

# 1. Charger les donnees preparees depuis S3
response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PROCESSED_PREFIX)
keys = [
    obj["Key"] for obj in response.get("Contents", [])
    if obj["Key"].lower().endswith(".csv")
]

if len(keys) != 1:
    raise RuntimeError(
        f"Un seul CSV est attendu dans {PROCESSED_PREFIX}, trouves : {keys}"
    )

obj = s3.get_object(Bucket=BUCKET, Key=keys[0])
df = pd.read_csv(io.BytesIO(obj["Body"].read()))

if "target" not in df.columns:
    raise ValueError("La colonne target est absente.")

if df.isnull().any().any():
    raise ValueError("Le dataset contient des valeurs manquantes.")

if set(df["target"].unique()) != {0, 1}:
    raise ValueError("La colonne target doit contenir les classes 0 et 1.")

X = df.drop(columns=["target"])
y = (df["target"] == 0).astype(int)  # 1 = malin, 0 = benin

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 2. Modele de reference
baseline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", LogisticRegression(max_iter=2000, random_state=42)),
])
baseline.fit(X_train, y_train)


def f1_malignant_score(y_true, y_pred):
    return f1_score(y_true, y_pred, zero_division=0)


def recall_malignant_score(y_true, y_pred):
    return recall_score(y_true, y_pred, zero_division=0)


scoring = {
    "f1_malignant": make_scorer(f1_malignant_score),
    "recall_malignant": make_scorer(recall_malignant_score),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# 3. Recherche des hyperparametres Random Forest
rf_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [None, 10, 20],
    "min_samples_leaf": [1, 2, 4],
    "max_features": ["sqrt", 0.5],
    "class_weight": ["balanced", "balanced_subsample"],
}

rf_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    rf_grid,
    scoring=scoring,
    refit=False,
    cv=cv,
    n_jobs=-1,
)
rf_search.fit(X_train, y_train)

# 4. Recherche des hyperparametres SVM
svm_pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", SVC(class_weight="balanced")),
])

svm_grid = {
    "model__C": [0.1, 1, 10],
    "model__kernel": ["rbf", "linear"],
    "model__gamma": ["scale", "auto"],
}

svm_search = GridSearchCV(
    svm_pipeline,
    svm_grid,
    scoring=scoring,
    refit=False,
    cv=cv,
    n_jobs=-1,
)
svm_search.fit(X_train, y_train)


def select_best_params(search):
    results = search.cv_results_
    eligible = [
        i for i, recall in enumerate(results["mean_test_recall_malignant"])
        if recall >= MINIMUM_RECALL
    ]

    if not eligible:
        return None

    best = max(
        eligible,
        key=lambda i: results["mean_test_f1_malignant"][i],
    )
    return results["params"][best]


rf_params = select_best_params(rf_search)
svm_params = select_best_params(svm_search)

# 5. Entrainer les candidats
candidates = {}

if rf_params is not None:
    model = RandomForestClassifier(**rf_params, random_state=42)
    model.fit(X_train, y_train)
    candidates["random_forest"] = {"model": model, "params": rf_params}

if svm_params is not None:
    model = clone(svm_pipeline).set_params(**svm_params)
    model.fit(X_train, y_train)
    candidates["svm"] = {"model": model, "params": svm_params}


def evaluate(model):
    predictions = model.predict(X_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "recall_malignant": round(float(
            recall_score(y_test, predictions, zero_division=0)
        ), 4),
        "f1_malignant": round(float(
            f1_score(y_test, predictions, zero_division=0)
        ), 4),
    }


baseline_metrics = evaluate(baseline)

candidate_metrics = {
    name: evaluate(info["model"])
    for name, info in candidates.items()
}

# 6. Verifier les criteres d'approbation
# Sauvegarder tous les candidats entraînés, même rejetés
candidate_dir = MODEL_DIR / "candidates"
candidate_dir.mkdir(parents=True, exist_ok=True)
approved_dir = MODEL_DIR / "approved"
approved_dir.mkdir(parents=True, exist_ok=True)
approved_path = approved_dir / "approved_model.joblib"

# Sauvegarder tous les candidats
for name, info in candidates.items():
    joblib.dump(info["model"], candidate_dir / f"{name}.joblib")

# Candidats éligibles, triés par F1 décroissant
eligible_candidates = sorted(
    [n for n, m in candidate_metrics.items()
     if m["recall_malignant"] >= MINIMUM_RECALL],
    key=lambda n: candidate_metrics[n]["f1_malignant"],
    reverse=True,
)

approved = False
selected_candidate = None

for name in eligible_candidates:
    approved = promote_if_approved(
        baseline_metrics,
        candidate_metrics[name],
        candidate_dir / f"{name}.joblib",
        approved_path,
        minimum_recall=MINIMUM_RECALL,
    )
    if approved:
        selected_candidate = name
        break
 

# 7. Definir le modele actif
if approved:
    active_model = selected_candidate
    active_model_path = approved_path
else:
    active_model = "baseline"
    active_model_path = MODEL_DIR / "production_model.joblib"
    joblib.dump(baseline, active_model_path)

# 8. Publier le modele actif dans S3
active_model_s3_key = "models/production/model.joblib"

s3.upload_file(
    str(active_model_path),
    BUCKET,
    active_model_s3_key,
)

active_model_artifact = f"s3://{BUCKET}/{active_model_s3_key}"

# 9. Enregistrer le rapport d'evaluation
results = {
    "dataset": keys[0],
    "rows": int(len(df)),
    "features": int(X.shape[1]),
    "baseline": baseline_metrics,
    "candidates": candidate_metrics,
    "best_params": {
        "random_forest": rf_params,
        "svm": svm_params,
    },
    "guardrails": {
        "minimum_recall_malignant": MINIMUM_RECALL,
        "eligible_candidates": eligible_candidates,
    },
    "selected_candidate": selected_candidate,
    "active_model": active_model,
    "active_model_artifact": active_model_artifact,
    "decision": "APPROVED" if approved else "REJECTED",
}

report_path = MODEL_DIR / "evaluation.json"

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

# 10. Envoyer les candidats vers S3
for name in candidates:
    path = candidate_dir / f"{name}.joblib"

    if path.exists():
        s3.upload_file(
            str(path),
            BUCKET,
            f"models/candidates/{name}.joblib",
        )

# Envoyer le candidat approuve, s'il existe
if approved and approved_path.exists():
    s3.upload_file(
        str(approved_path),
        BUCKET,
        "models/approved/approved_model.joblib",
    )

# Envoyer le rapport
s3.upload_file(
    str(report_path),
    BUCKET,
    "reports/evaluation.json",
)

print(json.dumps(results, indent=4))
