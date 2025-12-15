from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from fastapi.routing import APIRoute


class _Resp:
    """Tiny requests-like response stub for patching external HTTP calls."""

    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content


def test_api_happy_path_all_endpoints(patch_backend_deps, monkeypatch: pytest.MonkeyPatch):
    # Patch external network calls used by create + license-check routers.
    monkeypatch.setattr(
        "backend.api.create.requests.get",
        lambda *args, **kwargs: _Resp(status_code=200, content=b"artifact-bytes"),
    )
    monkeypatch.setattr(
        "backend.api.license_check.requests.head",
        lambda *args, **kwargs: _Resp(status_code=200, content=b""),
    )

    from backend.main import app

    # Ensure this test exercises every registered API route (excluding docs/openapi).
    skip_paths = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
    app_routes: set[tuple[str, str]] = set()
    for r in app.routes:
        if not isinstance(r, APIRoute):
            continue
        if r.path in skip_paths:
            continue
        for m in set(r.methods or set()) - {"HEAD", "OPTIONS"}:
            app_routes.add((m, r.path))

    client = TestClient(app)

    exercised: set[tuple[str, str]] = set()

    # health
    assert client.get("/health").status_code == 200
    exercised.add(("GET", "/health"))

    # create
    c = client.post("/artifact/model", json={"url": "https://github.com/o/r"})
    assert c.status_code == 201
    artifact_id = c.json()["metadata"]["id"]
    exercised.add(("POST", "/artifact/{artifact_type}"))

    # retrieve
    r = client.get(f"/artifacts/model/{artifact_id}")
    assert r.status_code == 200
    exercised.add(("GET", "/artifacts/{artifact_type}/{id}"))

    # rate
    rate = client.get(f"/artifact/model/{artifact_id}/rate")
    assert rate.status_code == 200
    assert "net_score" in rate.json()
    exercised.add(("GET", "/artifact/model/{id}/rate"))

    # lineage
    lin = client.get(f"/artifact/model/{artifact_id}/lineage")
    assert lin.status_code == 200
    assert "nodes" in lin.json()
    exercised.add(("GET", "/artifact/model/{id}/lineage"))

    # license-check
    lc = client.post(
        f"/artifact/model/{artifact_id}/license-check",
        json={"github_url": "https://github.com/o/r"},
    )
    assert lc.status_code == 200
    assert lc.json() is True
    exercised.add(("POST", "/artifact/model/{id}/license-check"))

    # cost
    cost = client.get(f"/artifact/model/{artifact_id}/cost")
    assert cost.status_code == 200
    assert artifact_id in cost.json()
    exercised.add(("GET", "/artifact/{artifact_type}/{id}/cost"))

    # byRegEx
    br = client.post("/artifact/byRegEx", json={"regex": "r"})
    assert br.status_code == 200
    exercised.add(("POST", "/artifact/byRegEx"))

    # list
    lst = client.post("/artifacts", json=[{"name": "*"}])
    assert lst.status_code == 200
    assert isinstance(lst.json(), list)
    exercised.add(("POST", "/artifacts"))

    # download
    dl = client.get(f"/artifact/{artifact_id}/download", follow_redirects=False)
    assert dl.status_code == 302
    assert dl.headers["location"].startswith("https://")
    exercised.add(("GET", "/artifact/{artifact_id}/download"))

    # update
    upd = client.put(f"/artifacts/model/{artifact_id}", json={"x": 1})
    assert upd.status_code == 200
    assert upd.json()["artifact_id"] == artifact_id
    exercised.add(("PUT", "/artifacts/{artifact_type}/{id}"))

    # delete
    d = client.delete(f"/artifacts/model/{artifact_id}")
    assert d.status_code == 200
    exercised.add(("DELETE", "/artifacts/{artifact_type}/{id}"))

    # reset
    rs = client.delete("/reset")
    assert rs.status_code == 200
    assert rs.json()["message"] == "Registry reset"
    exercised.add(("DELETE", "/reset"))

    assert exercised == app_routes
