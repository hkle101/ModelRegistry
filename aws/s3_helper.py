import json
import boto3
from aws.config import BUCKET_NAME, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN

# Initialize S3 client
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

def upload_model_metadata(model_name: str, scores: dict, url: str) -> str:
    """Upload a model's metadata JSON to S3."""
    metadata = {
        "Name": model_name,
        "Scores": scores,
        "url": url
    }

    key = f"{model_name}.json"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(metadata, indent=2),
        ContentType="application/json"
    )
    return f"s3://{BUCKET_NAME}/{key}"


def get_model_metadata(model_name: str) -> dict:
    key = f"{model_name}.json"
    response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    content = response["Body"].read().decode("utf-8")
    return json.loads(content)

def delete_model_metadata(model_name: str) -> None:
    key = f"{model_name}.json"
    s3.delete_object(Bucket=BUCKET_NAME, Key=key)

def list_models() -> list:
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    if "Contents" in response:
        return [obj["Key"].replace(".json", "") for obj in response["Contents"]]
    return []
