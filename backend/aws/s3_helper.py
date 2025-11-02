"""Small helper for interacting with S3 (placeholder).

This module provides simple stubs used by the scaffold to estimate
artifact sizes and simulate uploads. Replace with `boto3` calls in
production and secure credentials via environment/secret manager.
"""

from typing import Dict, Any, Optional
import os


def upload_to_s3(bucket: str, key: str, data: bytes) -> Dict[str, Any]:
    """Simulate uploading bytes to S3 and return metadata (placeholder).

    In a real deployment this would call boto3.client('s3').put_object(...)
    and return the S3 URL and metadata.
    """
    return {"bucket": bucket, "key": key, "size": len(data), "url": f"s3://{bucket}/{key}"}


def estimate_model_size(metadata: Dict[str, Any]) -> Optional[float]:
    """Estimate model size (MB) from provided metadata.

    Heuristic: look for common fields like `usedStorage`, `safetensors.total`,
    or `files` listing. Returns size in MB or None if unknown.
    """
    # Hugging Face API often exposes usedStorage (bytes)
    used = None
    if isinstance(metadata, dict):
        used = metadata.get("usedStorage")
        # check safetensors total
        safetensors = metadata.get("safetensors")
        if isinstance(safetensors, dict):
            val = safetensors.get("total")
            if val:
                used = val
        # some metadata may include sizes in siblings
        siblings = metadata.get("siblings")
        if used is None and isinstance(siblings, list):
            total = 0
            found = False
            for s in siblings:
                try:
                    size = int(s.get("size", 0) or 0)
                    total += size
                    found = True
                except Exception:
                    continue
            if found:
                used = total

    if used is None:
        return None

    try:
        mb = float(used) / (1024.0 * 1024.0)
        return round(mb, 2)
    except Exception:
        return None

