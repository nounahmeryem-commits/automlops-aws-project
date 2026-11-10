import json
import boto3

s3 = boto3.client("s3")

BUCKET = os.environ.get("BUCKET", "<your-bucket>")
KEY = "reports/evaluation.json"


def lambda_handler(event, context):
    response = s3.get_object(
        Bucket=BUCKET,
        Key=KEY
    )

    report = json.loads(
        response["Body"].read().decode("utf-8")
    )

    decision = report.get("decision")

    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError(
            f"Decision absente ou invalide : {decision}"
        )

    return {
        "decision": decision,
        "report_s3_uri": f"s3://{BUCKET}/{KEY}"
    }
