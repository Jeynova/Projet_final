import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.db import get_db
from src.models import Base

# Base de données en mémoire pour les tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def authenticated_client(client):
    # Créer un utilisateur et obtenir un token
    user_data = {"email": "test@example.com", "password": "testpass"}
    client.post("/auth/register", json=user_data)
    
    response = client.post("/auth/login", json=user_data)
    token = response.json()["access_token"]
    
    client.headers["Authorization"] = f"Bearer {token}"
    return client

def test_create_vehicle(authenticated_client):
    vehicle_data = {
        "license_plate": "ABC123",
        "make": "Toyota",
        "model": "Camry",
        "year": 2020
    }
    
    response = authenticated_client.post("/vehicles/", json=vehicle_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["license_plate"] == "ABC123"
    assert data["make"] == "Toyota"
    assert data["model"] == "Camry"
    assert data["year"] == 2020

def test_list_vehicles(authenticated_client):
    # Créer quelques véhicules
    vehicles = [
        {"license_plate": "ABC123", "make": "Toyota", "model": "Camry", "year": 2020},
        {"license_plate": "DEF456", "make": "Honda", "model": "Civic", "year": 2019}
    ]
    
    for vehicle in vehicles:
        authenticated_client.post("/vehicles/", json=vehicle)
    
    response = authenticated_client.get("/vehicles/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2

def test_get_vehicle(authenticated_client):
    vehicle_data = {"license_plate": "ABC123", "make": "Toyota", "model": "Camry", "year": 2020}
    create_response = authenticated_client.post("/vehicles/", json=vehicle_data)
    vehicle_id = create_response.json()["id"]
    
    response = authenticated_client.get(f"/vehicles/{vehicle_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == vehicle_id
    assert data["license_plate"] == "ABC123"

def test_update_vehicle(authenticated_client):
    vehicle_data = {"license_plate": "ABC123", "make": "Toyota", "model": "Camry", "year": 2020}
    create_response = authenticated_client.post("/vehicles/", json=vehicle_data)
    vehicle_id = create_response.json()["id"]
    
    update_data = {"year": 2021, "model": "Camry Hybrid"}
    response = authenticated_client.put(f"/vehicles/{vehicle_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["year"] == 2021
    assert data["model"] == "Camry Hybrid"

def test_delete_vehicle(authenticated_client):
    vehicle_data = {"license_plate": "ABC123", "make": "Toyota", "model": "Camry", "year": 2020}
    create_response = authenticated_client.post("/vehicles/", json=vehicle_data)
    vehicle_id = create_response.json()["id"]
    
    response = authenticated_client.delete(f"/vehicles/{vehicle_id}")
    assert response.status_code == 200
    
    # Vérifier que le véhicule n'existe plus
    get_response = authenticated_client.get(f"/vehicles/{vehicle_id}")
    assert get_response.status_code == 404

def test_unauthorized_access(client):
    response = client.get("/vehicles/")
    assert response.status_code == 200
    assert response.json() == []  # Empty list for unauthenticated users

def test_auth_endpoints(client):
    # Test register
    user_data = {"email": "test@example.com", "password": "testpass"}
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    
    # Test login
    response = client.post("/auth/login", json=user_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
