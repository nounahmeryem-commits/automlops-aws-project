
from pathlib import Path

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "approved_model.joblib"

app = FastAPI(
    title="AutoMLOps Lab API",
    description="API de prédiction avec contrôle du modèle approuvé.",
    version="1.0.0",
)


class PredictionInput(BaseModel):
    features: list[float] = Field(
        ...,
        min_length=1,
        description="Les 30 caractéristiques du dataset Breast Cancer, dans l'ordre original.",
    )


@app.get("/")
def home():
    return {
        "message": "AutoMLOps Lab API",
        "model_available": MODEL_PATH.is_file(),
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "approved_model_available": MODEL_PATH.is_file(),
    }


@app.post("/predict")
def predict(data: PredictionInput):
    if not MODEL_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="Aucun modèle approuvé disponible. Les candidats doivent d'abord passer les critères de promotion.",
        )

    try:
        model = joblib.load(MODEL_PATH)
        features = np.array(data.features, dtype=float).reshape(1, -1)

        if features.shape[1] != 30:
            raise HTTPException(
                status_code=400,
                detail=f"30 caractéristiques sont requises, {features.shape[1]} reçues.",
            )

        prediction = int(model.predict(features)[0])

        # Le modèle approuvé utilise la cible originale :
        # 0 = malin, 1 = bénin.
        label = "malin" if prediction == 0 else "benin"

        return {
            "prediction": prediction,
            "label": label,
            "model": "approved_model.joblib",
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur pendant la prédiction : {str(exc)}",
        ) from exc
