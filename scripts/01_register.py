"""
Testing:
  - Registering a new user (success)
  - Attempting to register the same email again (duplicate email error)
  - Attempting to register the same username again (duplicate username error)

Run: python scripts/01_register.py
Requires the API to be running at http://localhost:8000
"""

import requests

BASE_URL = "http://localhost:8000"

USER = {
    "username": "ljusup",
    "email": "ljusup@example.com",
    "password": "secret123",
}


def print_response(label, response):
    print(f"\n{'─' * 55}")
    print(f"  {label}")
    print(f"  Status : {response.status_code}")
    print(f"  Body   : {response.json()}")
    print(f"{'─' * 55}")


# 1. Register a new user
print("\n[1] Registering a new user...")
resp = requests.post(f"{BASE_URL}/auth/register", json=USER)
print_response("POST /auth/register - new user", resp)

if resp.status_code == 201:
    print("  OK - User created successfully.")
else:
    print("  ERROR - Unexpected error.")


# 2. Try to register with the same email
print("\n[2] Trying to register with the same email again...")
resp = requests.post(
    f"{BASE_URL}/auth/register",
    json={**USER, "username": "ljusup2"},
)
print_response("POST /auth/register - duplicate email", resp)

if resp.status_code == 400:
    print("  OK - Correctly rejected: email already registered.")


# 3. Try to register with the same username
print("\n[3] Trying to register with the same username again...")
resp = requests.post(
    f"{BASE_URL}/auth/register",
    json={**USER, "email": "ljusup2@example.com"},
)
print_response("POST /auth/register - duplicate username", resp)

if resp.status_code == 400:
    print("  OK - Correctly rejected: username already taken.")