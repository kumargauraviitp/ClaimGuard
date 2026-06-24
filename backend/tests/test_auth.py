import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_login_invalid_credentials():
    response = client.post("/auth/login", json={"username": "admin", "password": "wrong_password"})
    assert response.status_code in [401, 403]

def test_protected_route_without_token():
    # Since claims endpoints are protected, calling one without a token should fail
    response = client.get("/api/claims")
    assert response.status_code == 401
