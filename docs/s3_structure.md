# Structure du bucket S3

Bucket : `s3://<your-bucket>/`

```
<your-bucket>/
├── code/
│   ├── launcher.py                 # Point d'entrée SageMaker Processing
│   └── src/training/pipeline.py    # Pipeline d'entraînement et d'évaluation
├── data/
│   └── processed/                  # CSV utilisés par le pipeline
├── models/
│   ├── candidates/                 # Tous les modèles candidats entraînés
│   ├── approved/                   # Modèle candidat approuvé
│   └── production/                 # Modèle actuellement actif
└── reports/
    └── evaluation.json             # Métriques et décision (APPROVED / REJECTED)
```

## Rôle de chaque préfixe

| Préfixe | Écrit par | Lu par |
|---|---|---|
| `code/` | Toi (upload depuis le dépôt) | SageMaker (`launcher.py`) |
| `data/processed/` | Glue / upload manuel | Pipeline ML |
| `models/candidates/` | Pipeline ML | Pipeline ML |
| `models/approved/` | Pipeline ML | Pipeline ML |
| `models/production/` | Pipeline ML | Consommateurs du modèle |
| `reports/` | Pipeline ML | Lambda `read_evaluation` |

## Permissions nécessaires
- Rôle SageMaker : lecture `code/` et `data/`, écriture `models/` et `reports/`
- Lambda `read_evaluation` : `s3:GetObject` sur `reports/*`
- Rôle Glue : lecture/écriture sur `data/`
