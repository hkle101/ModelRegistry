"""Small script that performs health checks against the backend endpoints."""

import requests


def ping(url: str) -> bool:
    try:
        r = requests.get(url, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


if __name__ == "__main__":
    print("Health check not run automatically in scaffold")
