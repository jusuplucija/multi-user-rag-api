import requests

BASE_URL = "http://localhost:8000"

# --- configure these ---
EMAIL = "ljusup@example.com"
PASSWORD = "secret123"
FILE_PATH = r"C:\Users\Mirjana\Downloads\archive\Pdf\f55a8d69c6047f9037f79225c367766987e25f2b.pdf"  # path to your file on disk
# -----------------------

# 1. Login
resp = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
resp.raise_for_status()
token = resp.json()["access_token"]
print(f"Logged in. Token (first 60 chars): {token[:60]}...")

headers = {"Authorization": f"Bearer {token}"}

# 2. Upload the file
with open(FILE_PATH, "rb") as f:
    filename = FILE_PATH.split("\\")[-1]
    content_type = "application/pdf" if filename.endswith(".pdf") else "text/plain"
    resp = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files={"file": (filename, f, content_type)},
    )

print(f"Status : {resp.status_code}")
print(f"Body   : {resp.json()}")
