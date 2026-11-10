
import sys

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "INPUT_S3_PATH"]
)

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Chemins S3
BUCKET = os.environ.get("BUCKET", "<your-bucket>")
INPUT_PATH = args["INPUT_S3_PATH"]
OUTPUT_PATH = f"s3://{BUCKET}/data/processed/"

# 1. Lire les données brutes
df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(INPUT_PATH)
)

initial_count = df.count()
print(f"Nombre de lignes initial : {initial_count}")
print(f"Nombre de colonnes : {len(df.columns)}")

if initial_count == 0:
    raise ValueError("Le dataset brut est vide.")

if "target" not in df.columns:
    raise ValueError("La colonne target est absente.")

# 2. Vérifier les valeurs de la cible
invalid_targets = df.filter(
    F.col("target").isNull()
    | (~F.col("target").isin(0, 1))
).limit(1).count()

if invalid_targets:
    raise ValueError("La cible contient des valeurs nulles ou invalides.")

# 3. Vérifier les valeurs manquantes
null_condition = None

for column in df.columns:
    condition = F.col(column).isNull()

    if df.schema[column].dataType.typeName() in ("double", "float"):
        condition = condition | F.isnan(F.col(column))

    null_condition = (
        condition if null_condition is None
        else null_condition | condition
    )

missing_count = df.filter(null_condition).count()
print(f"Lignes avec valeurs manquantes : {missing_count}")

if missing_count > 0:
    raise ValueError(
        "Valeurs manquantes détectées. "
        "Définir une stratégie de traitement avant de continuer."
    )

# 4. Supprimer les lignes exactement dupliquées
prepared_df = df.dropDuplicates()

final_count = prepared_df.count()
print(f"Lignes après déduplication : {final_count}")
print(f"Doublons supprimés : {initial_count - final_count}")

# 5. Écrire les données préparées dans S3
(
    prepared_df.coalesce(1)
    .write
    .mode("overwrite")
    .option("header", True)
    .csv(OUTPUT_PATH)
)

print(f"Données préparées enregistrées dans : {OUTPUT_PATH}")

job.commit()

