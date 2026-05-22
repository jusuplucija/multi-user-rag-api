from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.document_service import document_service
from app.services.vector_store import vector_store_service

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf", "text/plain"}
MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Upload a PDF or plain-text file. The file is chunked, embedded, and stored in the vector database for later retrieval.",
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Accepted: application/pdf, text/plain.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {MAX_FILE_SIZE // (1024 * 1024)} MB limit.",
        )

    file_path = document_service.save_file(current_user.id, file.filename, content)

    doc = Document(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        content_type=file.content_type,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    document_service.process_and_index(
        current_user.id, doc.id, file_path, file.filename, file.content_type
    )

    return doc


@router.get(
    "/",
    response_model=list[DocumentResponse],
    summary="List my documents",
    description="Return all documents uploaded by the authenticated user.",
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Document).filter(Document.user_id == current_user.id).all()


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
    description="Delete a document and remove its chunks from the vector store.",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    vector_store_service.delete_document(current_user.id, document_id)
    document_service.delete_file(doc.file_path)
    db.delete(doc)
    db.commit()