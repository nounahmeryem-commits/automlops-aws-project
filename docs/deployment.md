# Déploiement

## Prérequis
- Compte AWS et AWS CLI configurée (`aws configure`)
- Région utilisée : `<region>`
- Bucket S3 : `<your-bucket>`

## Étapes
1. **SNS** : créer le topic et l'abonnement (voir `sns/`), confirmer l'email reçu.
2. **Lambdas** : déployer `trigger_glue` et `read_evaluation`.
   - Variable d'environnement de `read_evaluation` : `TOPIC_ARN`
3. **Glue** : créer le job avec `glue/automlops_ml_pipeline.py`.
4. **Step Functions** : créer la state machine à partir de `stepfunctions/state_machine.json`.
5. **EventBridge** : créer la règle avec `eventbridge/rule_pattern.json`.

## Permissions IAM
- Lambda `read_evaluation` : `s3:GetObject`, `sns:Publish`
- Lambda `trigger_glue` : `glue:StartJobRun`
- Rôle Step Functions : droits Glue et SageMaker
- Rôle SageMaker : accès S3

## Valeurs à remplacer
`<region>`, `<account_id>`, `<your-bucket>`, `<your-email@example.com>`
