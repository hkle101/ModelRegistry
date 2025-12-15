"""AWS and application configuration.

Loads environment variables and initializes AWS clients/resources used by the
backend.
"""

# core/config.py
from dotenv import load_dotenv
import os
import boto3
import logging

load_dotenv()

# --- AWS Configuration ---
AWS_REGION = "us-east-2"
BUCKET_NAME = "artifacts-for-modelregistry"
DYNAMODB_TABLE_NAME = "Artifacts"

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

session = boto3.Session(
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

s3 = session.client("s3")
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# --- Tokens ---
UPLOAD_TOKEN = os.getenv("UPLOAD_TOKEN", "default_upload_token")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "default_admin_token")

# --- Paths ---
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../../frontend")
LOG_DIR = os.path.join(os.path.dirname(__file__), "../../logs")

# --- Logger Setup ---


def get_logger(name="backend"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
    return logger


