# Dataset

Le dataset n'est pas versionné dans ce dépôt.

- **Nom** : Breast Cancer Wisconsin (Diagnostic)
- **Source** : UCI Machine Learning Repository (Wolberg, Street, Mangasarian), également disponible via `sklearn.datasets.load_breast_cancer`
- **Licence** : CC BY 4.0 (UCI)
- **Emplacement** : `s3://<your-bucket>/raw/breast_cancer.csv`
- **Taille** : 569 lignes, 30 variables + 1 cible

## Description
Les variables sont calculées à partir d'images numérisées d'une ponction à l'aiguille fine (FNA) d'une masse mammaire. Elles décrivent les caractéristiques des noyaux cellulaires.

## Cible
| Valeur | Signification | Effectif |
|---|---|---|
| Malin (M) | Tumeur maligne | 212 |
| Bénin (B) | Tumeur bénigne | 357 |

Avec scikit-learn, la cible est codée `0` = malin et `1` = bénin.

## Variables
10 caractéristiques, chacune déclinée en 3 statistiques (moyenne, erreur standard, pire valeur), soit 30 colonnes :

| Caractéristique | Description |
|---|---|
| radius | Rayon moyen du noyau |
| texture | Écart-type des niveaux de gris |
| perimeter | Périmètre |
| area | Aire |
| smoothness | Variation locale de la longueur des rayons |
| compactness | Périmètre² / aire − 1 |
| concavity | Gravité des parties concaves du contour |
| concave points | Nombre de parties concaves du contour |
| symmetry | Symétrie |
| fractal dimension | Approximation du « littoral » − 1 |

Exemples de colonnes : `mean radius`, `radius error`, `worst radius`.

## Obtenir les données
```python
from sklearn.datasets import load_breast_cancer
df = load_breast_cancer(as_frame=True).frame
df.to_csv("breast_cancer.csv", index=False)
```
