def test_register_success(client):
    resp = client.post("/auth/register", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "bob@example.com"
    assert data["username"] == "bob"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json={**payload, "username": "bob2"})
    assert resp.status_code == 400
    assert "Email" in resp.json()["detail"]


def test_register_duplicate_username(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json={**payload, "email": "other@example.com"})
    assert resp.status_code == 400
    assert "Username" in resp.json()["detail"]


def test_login_success(client, registered_user):
    resp = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user):
    resp = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert resp.status_code == 401


def test_get_me(client, auth_headers, registered_user):
    resp = client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == registered_user["email"]


def test_get_me_unauthenticated(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"