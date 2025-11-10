# config.py
from dotenv import load_dotenv
import os
import boto3

load_dotenv()  # Load secrets from .env

# --- Core AWS configuration ---
AWS_REGION = "us-east-2"
BUCKET_NAME = "model-metadata-bucket"
DYNAMODB_TABLE_NAME = "Artifacts"

# Optional if you’re using IAM Role on EC2 (recommended)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# --- Initialize clients once ---
session = boto3.Session(
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

s3 = session.client("s3")
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

