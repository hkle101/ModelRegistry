"""License checking utilities.

Analyze license metadata and return compatibility flags.
"""

from typing import Dict, Any


def is_license_compatible(license_str: str) -> bool:
    """Return True for compatible licenses (placeholder logic)."""
    return "MIT" in (license_str or "")
