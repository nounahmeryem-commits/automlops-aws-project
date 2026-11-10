# Format de l'évaluation

Le job SageMaker écrit `evaluation.json` dans `s3://<your-bucket>/evaluation/`.

```json
{
  "accuracy": number1,
  "f1_score": number2 ,
  "model_version": "v1"
}
```

| Champ | Description |
|---|---|
| `accuracy` | Part de prédictions correctes |
| `f1_score` | Moyenne harmonique précision/rappel |
| `model_version` | Version du modèle évalué |

La Lambda `read_evaluation` lit ce fichier et publie son contenu sur SNS.
