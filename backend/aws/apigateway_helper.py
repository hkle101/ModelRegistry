"""Helpers for building API Gateway payloads and responses."""

from typing import Dict, Any


def make_apigw_response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {"statusCode": status, "body": body}
