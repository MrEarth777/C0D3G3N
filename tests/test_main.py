import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from httpx import AsyncClient
from api import app, create_tables  # Correcte import

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# ✅ Test database-initialisatie
def test_database_initialization():
    try:
        create_tables()  # Roep create_tables() aan
    except Exception as e:
        pytest.fail(f"Database-initialisatie mislukt: {e}")

# ✅ Test registratie
@pytest.mark.anyio
async def test_register(client):
    response = await client.post("/register", json={"username": "testuser", "password": "1234"})
    assert response.status_code in [200, 400]  # 400 als gebruiker al bestaat
    assert "message" in response.json()

# ✅ Test login en token generatie
@pytest.mark.anyio
async def test_login(client):
    response = await client.post("/token", data={"username": "testuser", "password": "1234"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    return response.json()["access_token"]

# ✅ Test toegang tot beschermde route met geldig token
@pytest.mark.anyio
async def test_protected_route(client):
    token = await test_login(client)
    headers = {"Authorization": token}
    response = await client.get("/protected", headers=headers)
    assert response.status_code == 200
    assert "Welkom" in response.json()["message"]

# ✅ Test toegang tot beschermde route met ongeldige token
@pytest.mark.anyio
async def test_protected_route_invalid_token(client):
    headers = {"Authorization": "Bearer fake-token"}
    response = await client.get("/protected", headers=headers)
    assert response.status_code == 401
