import requests

url = "http://localhost:8000/auth/login"

payload = {
    "email": "lucija@example.com",
    "password": "123456"
}

response = requests.post(url, json=payload)

# print(response.status_code)
# print(response.access)
data = response.json()
access_token = data["access_token"]
token_type = data["token_type"]

print(access_token)
print(token_type)


# AUTHORIZE
jwt_token = access_token

url = "http://localhost:8000/query/"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
payload = {
    "query": "",
    "top_k": 5
}

response = requests.post(url, headers=headers, json=payload)

print(response.status_code)
print(response.json())