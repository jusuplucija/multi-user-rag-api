# Multi-User RAG API

A production-ready REST API that lets each user upload their own documents and query them with Retrieval-Augmented Generation (RAG). Built with FastAPI, ChromaDB, LangChain, and PostgreSQL, fully containerised with Docker Compose.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   FastAPI App                   │
│  /auth  │  /users  │  /documents  │  /query     │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   PostgreSQL                 ChromaDB
  (users, documents          (per-user vector
     metadata)                 collections)
        │
   Local storage
   (uploaded files)
```

**Per-user isolation** is enforced at every layer:
- SQL queries always filter by `user_id`
- ChromaDB uses a separate collection per user (`user_<id>`)
- Uploaded files are stored under `storage/<user_id>/`

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Relational DB | PostgreSQL (SQLite for local dev) |
| ORM | SQLAlchemy |
| Auth | JWT (python-jose) + bcrypt |
| Vector DB | ChromaDB (persistent, embedded) |
| Embeddings | `all-MiniLM-L6-v2` via sentence-transformers |
| RAG / LLM | LangChain + OpenAI `gpt-3.5-turbo` (primary) or Ollama `llama3.2` (local fallback) |
| Document loading | LangChain (PyPDFLoader, TextLoader) |
| Containerisation | Docker + Docker Compose |

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Register a new user |
| POST | `/auth/login` | — | Login, receive JWT |
| GET | `/users/me` | ✓ | Get current user info |
| POST | `/documents/upload` | ✓ | Upload a PDF or .txt file |
| GET | `/documents/` | ✓ | List your documents |
| DELETE | `/documents/{id}` | ✓ | Delete a document |
| POST | `/query/` | ✓ | RAG query over your documents |
| GET | `/health` | — | Health check |

Full OpenAPI spec available at **`/docs`** (Swagger UI) after starting the app.

---

## Quickstart with Docker Compose

```bash
# 1. Copy and configure environment variables
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY (optional — retrieval works without it)

# 2. Build and start all services
docker compose up --build

# 3. API available at http://localhost:8000
# 4. Swagger UI at http://localhost:8000/docs
```

Docker Compose starts:
- **api** — FastAPI on port 8000
- **db** — PostgreSQL 15
- **ollama** — local LLM server on port 11434

ChromaDB runs embedded inside the API container with a persistent volume.

> **First-time startup note:** the `ollama` container automatically pulls `llama3.2` (~2 GB) on first boot. The API is available immediately; `/query/` returns retrieved context until the model finishes downloading, then switches to full LLM responses automatically.

---

## Local Development (without Docker)

### Prerequisites

- Python 3.11+
- SQLite (included with Python)

### Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment (SQLite is used by default)
cp .env.example .env
# Set SECRET_KEY and optionally OPENAI_API_KEY in .env

# Run the API
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`, Swagger UI at `http://localhost:8000/docs`.

---

## Running Tests

Activate your virtual environment first, then run from the project root:

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run only auth tests
pytest tests/test_auth.py -v

# Run only document/query tests
pytest tests/test_documents.py -v

# Run a single test by name
pytest tests/test_auth.py::test_login_success -v
```

Tests use an isolated SQLite database (created and destroyed per test function) and mock the vector store and file services, so they run fast and require no external dependencies.

### What is covered

| Category | Tests |
|---|---|
| **Happy path** | register, login, get current user, upload document, list documents, delete document, query with answer |
| **Validation errors** | unsupported file type (415), file too large (413) |
| **Authentication** | all protected endpoints return 401 when called without a token |
| **Authorization** | user cannot delete another user's document (404) |
| **Per-user isolation** | user B cannot see documents uploaded by user A |
| **Edge cases** | query when no documents have been uploaded |

---

## Example Usage

### 1. Register and login

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "secret123"}'

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "secret123"}'
# → { "access_token": "<JWT>", "token_type": "bearer" }
```

### 2. Upload a document

```bash
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer <JWT>" \
  -F "file=@my_document.pdf"
```

### 3. Query your documents

```bash
curl -X POST http://localhost:8000/query/ \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main conclusions?", "top_k": 5}'
```

---

## Configuration

All settings are read from `.env`:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | JWT signing key (required) |
| `DATABASE_URL` | `sqlite:///./test.db` | SQLAlchemy DB URL |
| `OPENAI_API_KEY` | `""` | OpenAI key — used if set; falls back to Ollama otherwise |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL (auto-set to `http://ollama:11434` in Docker) |
| `OLLAMA_MODEL` | `llama3.2` | Ollama model name |
| `VECTOR_DB_PATH` | `./chroma_db` | ChromaDB persistence directory |
| `STORAGE_PATH` | `./storage` | Uploaded file directory |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT expiry |

**LLM priority:** if `OPENAI_API_KEY` is set it is used; otherwise Ollama is used. If Ollama is also unavailable (e.g. during local dev without installing it), the raw retrieved context is returned as a fallback.