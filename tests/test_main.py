import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from unittest.mock import patch

client = TestClient(app)

def test_upload_endpoint():
    with patch("backend.app.main.upload_model", return_value="s3://bucket/m1.json"):
        response = client.post("/upload", json={"model_url": "url"})
        assert response.status_code == 200
        assert response.json() == {"s3_path": "s3://bucket/m1.json"}

def test_list_endpoint():
    with patch("backend.app.main.list_models", return_value=["m1", "m2"]):
        response = client.get("/models")
        assert response.status_code == 200
        assert "m1" in response.json()

def test_get_endpoint():
    with patch("backend.app.main.get_model", return_value={"Name": "m1"}):
        response = client.get("/models/m1")
        assert response.status_code == 200
        assert response.json()["Name"] == "m1"

def test_delete_endpoint():
    with patch("backend.app.main.delete_model", return_value=True):
        response = client.delete("/models/m1")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
