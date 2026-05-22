from unittest.mock import MagicMock, patch

SAMPLE_TEXT = (
    "Artificial intelligence (AI) is intelligence demonstrated by machines. "
    "Machine learning is a subset of AI that enables systems to learn from data. "
    "Deep learning uses neural networks with many layers to model complex patterns. " * 20
)


def _upload(client, headers, content=SAMPLE_TEXT.encode(), filename="doc.txt", ctype="text/plain"):
    return client.post(
        "/documents/upload",
        files={"file": (filename, content, ctype)},
        headers=headers,
    )


@patch("app.api.documents.document_service.save_file", return_value="/tmp/doc.txt")
@patch("app.api.documents.document_service.process_and_index")
def test_upload_document(mock_index, mock_save, client, auth_headers):
    resp = _upload(client, auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "doc.txt"
    assert data["content_type"] == "text/plain"
    assert "id" in data
    mock_save.assert_called_once()
    mock_index.assert_called_once()


@patch("app.api.documents.document_service.save_file", return_value="/tmp/doc.txt")
@patch("app.api.documents.document_service.process_and_index")
def test_upload_unsupported_type(mock_index, mock_save, client, auth_headers):
    resp = client.post(
        "/documents/upload",
        files={"file": ("file.csv", b"a,b,c", "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 415


def test_upload_file_too_large(client, auth_headers):
    oversized = b"x" * (30 * 1024 * 1024 + 1)  # 1 byte over 30 MB limit
    resp = client.post(
        "/documents/upload",
        files={"file": ("big.txt", oversized, "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 413


@patch("app.api.documents.document_service.save_file", return_value="/tmp/doc.txt")
@patch("app.api.documents.document_service.process_and_index")
def test_upload_requires_auth(mock_index, mock_save, client):
    resp = _upload(client, {})
    assert resp.status_code == 401


@patch("app.api.documents.document_service.save_file", return_value="/tmp/doc.txt")
@patch("app.api.documents.document_service.process_and_index")
def test_list_documents(mock_index, mock_save, client, auth_headers):
    _upload(client, auth_headers, filename="a.txt")
    _upload(client, auth_headers, filename="b.txt")
    resp = client.get("/documents/", headers=auth_headers)
    assert resp.status_code == 200
    names = [d["filename"] for d in resp.json()]
    assert "a.txt" in names
    assert "b.txt" in names


@patch("app.api.documents.document_service.save_file", return_value="/tmp/doc.txt")
@patch("app.api.documents.document_service.process_and_index")
def test_user_isolation(mock_index, mock_save, client):
    # Register two users and verify they cannot see each other's documents
    client.post("/auth/register", json={"username": "u1", "email": "u1@x.com", "password": "pass123"})
    client.post("/auth/register", json={"username": "u2", "email": "u2@x.com", "password": "pass123"})

    def login(email):
        r = client.post("/auth/login", json={"email": email, "password": "pass123"})
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    h1, h2 = login("u1@x.com"), login("u2@x.com")
    _upload(client, h1, filename="private.txt")

    assert client.get("/documents/", headers=h2).json() == []


@patch("app.api.documents.document_service.save_file", return_value="/tmp/doc.txt")
@patch("app.api.documents.document_service.process_and_index")
@patch("app.api.documents.vector_store_service.delete_document")
@patch("app.api.documents.document_service.delete_file")
def test_delete_document(mock_del_file, mock_del_vec, mock_index, mock_save, client, auth_headers):
    upload_resp = _upload(client, auth_headers)
    doc_id = upload_resp.json()["id"]

    resp = client.delete(f"/documents/{doc_id}", headers=auth_headers)
    assert resp.status_code == 204

    listed = client.get("/documents/", headers=auth_headers).json()
    assert all(d["id"] != doc_id for d in listed)


@patch("app.api.documents.document_service.save_file", return_value="/tmp/doc.txt")
@patch("app.api.documents.document_service.process_and_index")
@patch("app.api.documents.vector_store_service.delete_document")
@patch("app.api.documents.document_service.delete_file")
def test_delete_other_users_document(mock_del_file, mock_del_vec, mock_index, mock_save, client, auth_headers):
    client.post("/auth/register", json={"username": "eve", "email": "eve@x.com", "password": "pass123"})
    eve_token = client.post("/auth/login", json={"email": "eve@x.com", "password": "pass123"}).json()["access_token"]
    eve_headers = {"Authorization": f"Bearer {eve_token}"}

    upload_resp = _upload(client, auth_headers)
    doc_id = upload_resp.json()["id"]

    resp = client.delete(f"/documents/{doc_id}", headers=eve_headers)
    assert resp.status_code == 404


def test_query_no_documents(client, auth_headers):
    with patch("app.api.query.rag_service.query") as mock_query:
        mock_query.return_value = {
            "query": "What is AI?",
            "answer": "No documents found. Please upload documents before querying.",
            "sources": [],
        }
        resp = client.post("/query/", json={"query": "What is AI?"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["sources"] == []


def test_query_with_answer(client, auth_headers):
    with patch("app.api.query.rag_service.query") as mock_query:
        mock_query.return_value = {
            "query": "What is machine learning?",
            "answer": "Machine learning is a subset of AI.",
            "sources": ["doc.txt"],
        }
        resp = client.post("/query/", json={"query": "What is machine learning?"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Machine learning is a subset of AI."
    assert "doc.txt" in data["sources"]


def test_query_requires_auth(client):
    resp = client.post("/query/", json={"query": "hello"})
    assert resp.status_code == 401