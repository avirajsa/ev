import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["system"] == "EV-Backend"

def test_list_devices_endpoint():
    headers = {"Authorization": "Bearer ev_device_shared_secret_token_12345"}
    response = client.get("/api/v1/devices", headers=headers)
    assert response.status_code == 200
    assert "devices" in response.json()

def test_web_docs_endpoint():
    response = client.get("/docs-site/")
    assert response.status_code == 200
    assert "EV System" in response.text
