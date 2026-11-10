import os
import logging
import urllib.parse
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue = boto3.client("glue", region_name=os.environ.get("AWS_REGION", "eu-north-1"))

GLUE_JOB_NAME = os.environ.get("GLUE_JOB_NAME", "automlops-ml-pipeline")
RAW_PREFIX = "data/raw/"


def lambda_handler(event, context):
    results = []

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        # On ne traite que les CSV déposés dans data/raw/
        if not key.startswith(RAW_PREFIX) or not key.lower().endswith(".csv"):
            logger.info("Fichier ignoré : %s", key)
            continue

        input_path = f"s3://{bucket}/{key}"


        try:
            response = glue.start_job_run(
                JobName=GLUE_JOB_NAME,
                Arguments={
                    "--INPUT_S3_PATH": input_path
                },
            )
            logger.info("Glue Job lancé : %s pour %s", response["JobRunId"], input_path)
            results.append({"input": input_path, "job_run_id": response["JobRunId"]})

        except ClientError as e:
            logger.error("Échec du lancement Glue pour %s : %s", input_path, e)
            raise  # permet à Lambda de réessayer

    return {"statusCode": 200, "runs": results}
