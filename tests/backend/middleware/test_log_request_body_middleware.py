from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.main import LogRequestBodyMiddleware


def test_log_request_body_middleware_preserves_body_for_downstream():
    app = FastAPI()
    app.add_middleware(LogRequestBodyMiddleware)

    @app.post("/echo")
    async def echo(request: Request):
        body = await request.body()
        return {"body": body.decode("utf-8")}

    client = TestClient(app)
    res = client.post("/echo", json={"a": 1})
    assert res.status_code == 200
    assert '"a"' in res.json()["body"]
