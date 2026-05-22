from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.query import router as query_router
from app.api.users import router as users_router
from app.core.config import settings
from app.db.database import Base, engine
from app.models import Document, User  # noqa: F401 — ensures tables are registered

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="REST API for user authentication, document upload, and retrieval-augmented generation.",
    version=settings.app_version,
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(query_router)


@app.get("/", tags=["Health"])
def read_root():
    return {"message": f"{settings.app_name} is running"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}