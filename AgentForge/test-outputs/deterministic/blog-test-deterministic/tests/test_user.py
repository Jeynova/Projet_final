from fastapi.testclient import TestClient
from ..src.main import app

client = TestClient(app)

def test_get_users():
    """Test récupération liste users"""
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_user():
    """Test création user"""
    test_data = {"name": "test"}
    response = client.post("/users", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
