"""
Testing:
  - Logging in and receiving a JWT token
  - Fetching the current user profile
  - Listing documents with pagination and sorting
  - Filtering documents by filename

Run: python scripts/02_list_documents.py
Requires the API to be running at http://localhost:8000
Run 01_register.py first to create the user.
"""

import requests

BASE_URL = "http://localhost:8000"

CREDENTIALS = {
    "email": "lucija@example.com",
    "password": "123456",
}


def print_response(label, response):
    print(f"\n{'─' * 55}")
    print(f"  {label}")
    print(f"  Status : {response.status_code}")
    print(f"  Body   : {response.json()}")
    print(f"{'─' * 55}")


# 1. Login
print("\n[1] Logging in...")
resp = requests.post(f"{BASE_URL}/auth/login", json=CREDENTIALS)
print_response("POST /auth/login", resp)

if resp.status_code != 200:
    print("  ERROR - Login failed. Run 01_register.py first.")
    raise SystemExit(1)

token = resp.json()["access_token"]
print(f"\n  OK - Login successful.")
print(f"  Token (first 60 chars): {token[:60]}...")

headers = {"Authorization": f"Bearer {token}"}


# 2. Get current user profile
print("\n[2] Fetching current user profile...")
resp = requests.get(f"{BASE_URL}/users/me", headers=headers)
print_response("GET /users/me", resp)


# 3. List documents — page 1, sorted by created_at descending
print("\n[3] Listing documents (page 1, sorted by created_at desc)...")
resp = requests.get(
    f"{BASE_URL}/documents/",
    headers=headers,
    params={"page": 1, "page_size": 10, "sort_by": "created_at", "sort_order": "desc"},
)
print_response("GET /documents/", resp)

data = resp.json()
print(f"\n  Total documents : {data['total']}")
print(f"  Page            : {data['page']}  |  page_size: {data['page_size']}")

if not data["items"]:
    print("\n  No documents uploaded yet.")
    print("  Upload a file via Swagger UI (POST /documents/upload) to see results here.")
else:
    print(f"\n  OK - Showing {len(data['items'])} of {data['total']} document(s):")
    for doc in data["items"]:
        print(f"    [{doc['id']}] {doc['filename']}  |  {doc['content_type']}  |  uploaded: {doc['created_at']}")


# 4. Filter by filename
print("\n[4] Filtering documents where filename contains 'report'...")
resp = requests.get(
    f"{BASE_URL}/documents/",
    headers=headers,
    params={"filename": "report"},
)
print_response("GET /documents/?filename=report", resp)
data = resp.json()
print(f"\n  Matched {data['total']} document(s) with 'report' in the filename.")


# 5. Filter by content type
print("\n[5] Filtering documents by content type 'application/pdf'...")
resp = requests.get(
    f"{BASE_URL}/documents/",
    headers=headers,
    params={"content_type": "application/pdf"},
)
print_response("GET /documents/?content_type=application/pdf", resp)
data = resp.json()
print(f"\n  Found {data['total']} PDF document(s).")