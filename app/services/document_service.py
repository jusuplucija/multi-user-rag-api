import uuid
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.vector_store import vector_store_service

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class DocumentService:
    """Handles file persistence, text extraction, chunking, and vector indexing."""

    def __init__(self):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )

    def save_file(self, user_id: int, filename: str, content: bytes) -> str:
        user_dir = Path(settings.storage_path) / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4()}_{filename}"
        file_path = user_dir / safe_name
        file_path.write_bytes(content)
        return str(file_path)

    def process_and_index(
        self,
        user_id: int,
        document_id: int,
        file_path: str,
        filename: str,
        content_type: str,
    ) -> None:
        if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")

        raw_docs = loader.load()
        chunks = self._splitter.split_documents(raw_docs)
        texts = [c.page_content for c in chunks if c.page_content.strip()]

        if texts:
            vector_store_service.add_chunks(user_id, document_id, texts, filename)

    def delete_file(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists():
            path.unlink()


document_service = DocumentService()