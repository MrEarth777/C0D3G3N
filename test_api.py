# test_api.py
import requests
import json

BASE_URL = "http://localhost:8000"

def test_healthcheck():
    response = requests.get(f"{BASE_URL}/healthcheck")
    assert response.status_code == 200
    assert response.json()["message"] == "API is working correctly!"

def test_register_and_login():
    # Use a unique username for testing; adjust as needed
    payload = {"username": "pytestuser", "password": "password123"}
    
    # Register user
    reg_response = requests.post(f"{BASE_URL}/register/", json=payload)
    assert reg_response.status_code in [200, 400]  # If user already exists, 400 is acceptable
    
    # Log in user
    login_response = requests.post(f"{BASE_URL}/login/", json=payload)
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data

if __name__ == "__main__":
    test_healthcheck()
    test_register_and_login()
    print("Backend tests passed!")
