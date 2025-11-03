from dotenv import load_dotenv
import os

load_dotenv()  # loads secrets from .env

BUCKET_NAME = "model-metadata-bucket"  # your bucket name
AWS_REGION = "us-east-2"               # your bucket region

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")