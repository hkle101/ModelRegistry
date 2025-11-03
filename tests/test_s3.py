import boto3
import pytest
from aws.config import (
    BUCKET_NAME,
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_SESSION_TOKEN,
)

@pytest.fixture(scope="module")
def s3_client():
    """Create an S3 client fixture for all tests."""
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
    )

def test_s3_connection(s3_client):
    """Test that S3 connection works and returns at least one bucket."""
    response = s3_client.list_buckets()
    assert "Buckets" in response, "Response should contain a 'Buckets' key"

    bucket_names = [b['Name'] for b in response['Buckets']]
    print("Buckets in your account:", bucket_names)
    
    # Verify that the expected bucket exists
    assert BUCKET_NAME in bucket_names, f"{BUCKET_NAME} should exist in S3"

def test_bucket_access(s3_client):
    """Test that you can access and list objects in your configured bucket."""
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
    
    # If the bucket is empty, Contents key may not exist
    if 'Contents' in response:
        print(f"Objects in {BUCKET_NAME}:", [obj['Key'] for obj in response['Contents']])
    else:
        print(f"No objects found in {BUCKET_NAME}.")
    
    # Just assert the call succeeded
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
