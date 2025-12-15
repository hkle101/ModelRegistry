"""Shared backend dependencies.

Holds singleton instances (managers) used across routers and a baseline
`verify_token` dependency.
"""

import logging
from fastapi import Header
from cli.utils.ArtifactManager import ArtifactManager
from backend.services.storage import StorageManager

logger = logging.getLogger(__name__)

# Shared managers used across routers.
artifact_manager = ArtifactManager()
storage_manager = StorageManager()


def verify_token(
    x_authorization: str = Header(default=None, convert_underscores=False),
) -> bool:
    """
    Baseline no-op authorization.
    The baseline spec requires no auth, but routers still include the
    `x-authorization` header for compatibility. This function simply
    accepts all requests.
    Args:
        x_authorization (str | None): Optional auth header (ignored).
    Returns:
        bool: Always True.
    """
    return True


__all__ = ["artifact_manager", "storage_manager", "verify_token"]