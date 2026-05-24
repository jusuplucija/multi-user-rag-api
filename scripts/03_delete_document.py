"""
Testing:
  - Logging in to get a JWT token
  - Listing documents to find a document ID
  - Deleting a document by ID
  - Verifying the document is gone by listing again

Run: python scripts/03_delete_document.py
Requires the API to be running at http://localhost:8000
Run 01_register.py first to create the user, then upload at least one
document via Swagger UI (POST /documents/upload) before running this script.
"""

import requests

BASE_URL = "http://localhost:8000"

CREDENTIALS = {
    "email": "ljusup@example.com",
    "password": "secret123",
}


def print_response(label, response):
    print(f"\n{'─' * 55}")
    print(f"  {label}")
    print(f"  Status : {response.status_code}")
    if response.text:
        try:
            print(f"  Body   : {response.json()}")
        except Exception:
            print(f"  Body   : {response.text}")
    else:
        print("  Body   : (empty - 204 No Content)")
    print(f"{'─' * 55}")


# 1. Login
print("\n[1] Logging in...")
resp = requests.post(f"{BASE_URL}/auth/login", json=CREDENTIALS)
print_response("POST /auth/login", resp)

if resp.status_code != 200:
    print("  ERROR - Login failed. Run 01_register.py first.")
    raise SystemExit(1)

token = resp.json()["access_token"]
print(f"\n  OK - Logged in successfully.")
headers = {"Authorization": f"Bearer {token}"}


# 2. List documents before deletion
print("\n[2] Listing documents before deletion...")
resp = requests.get(f"{BASE_URL}/documents/", headers=headers)
print_response("GET /documents/", resp)

data = resp.json()
documents = data["items"]

if not documents:
    print("\n  No documents to delete.")
    print("  Upload a file via Swagger UI (POST /documents/upload) first.")
    raise SystemExit(0)

print(f"\n  Found {data['total']} document(s):")
for doc in documents:
    print(f"    [{doc['id']}] {doc['filename']}")

target = documents[0]
target_id = target["id"]
print(f"\n  Will delete document [{target_id}]: {target['filename']}")


# 3. Delete the document
print(f"\n[3] Deleting document {target_id}...")
resp = requests.delete(f"{BASE_URL}/documents/{target_id}", headers=headers)
print_response(f"DELETE /documents/{target_id}", resp)

if resp.status_code == 204:
    print(f"\n  OK - Document [{target_id}] deleted successfully.")
else:
    print(f"\n  ERROR - Deletion failed.")
    raise SystemExit(1)


# 4. List documents after deletion to confirm
print("\n[4] Listing documents after deletion (verification)...")
resp = requests.get(f"{BASE_URL}/documents/", headers=headers)
print_response("GET /documents/", resp)

data = resp.json()
remaining_ids = [d["id"] for d in data["items"]]

if target_id not in remaining_ids:
    print(f"\n  OK - Confirmed: document [{target_id}] is no longer in the list.")
else:
    print(f"\n  ERROR - Document [{target_id}] still appears.")

print(f"  Documents remaining: {data['total']}")