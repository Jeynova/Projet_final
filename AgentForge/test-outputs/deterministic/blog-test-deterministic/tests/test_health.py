import pytest
import httpx

def test_health():
    # Test minimal en direct si l'API tourne déjà (docker compose up)
    # En CI, on utilisera 'pytest -q' à l'intérieur du conteneur api après build
    resp = httpx.get("http://localhost:8000/health", timeout=5.0)
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"