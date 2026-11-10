
import subprocess
import sys
import boto3
import os
from pathlib import Path

BUCKET = os.environ.get("BUCKET", "<your-bucket>")
REGION = "eu-north-1"

s3 = boto3.client("s3", region_name=REGION)

# Répertoire de travail dans le conteneur SageMaker Processing
workdir = Path("/opt/ml/processing/code")
workdir.mkdir(parents=True, exist_ok=True)

# Télécharger les fichiers Python depuis S3
response = s3.list_objects_v2(
    Bucket=BUCKET,
    Prefix="code/src/"
)

for obj in response.get("Contents", []):
    key = obj["Key"]

    if key.endswith(".py"):
        relative_path = key.removeprefix("code/")
        destination = workdir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        s3.download_file(
            BUCKET,
            key,
            str(destination)
        )

# Télécharger requirements.txt
s3.download_file(
    BUCKET,
    "code/requirements.txt",
    str(workdir / "requirements.txt")
)

# Installer les dépendances
subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "install",
    "-r",
    str(workdir / "requirements.txt")
])

# Configurer les imports Python
env = os.environ.copy()
env["PYTHONPATH"] = (
    str(workdir) + os.pathsep + env.get("PYTHONPATH", "")
)

# Exécuter le pipeline comme un module Python
subprocess.check_call(
    [sys.executable, "-m", "src.training.pipeline"],
    cwd=str(workdir),
    env=env
)

