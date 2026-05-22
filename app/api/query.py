from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.document import QueryRequest, QueryResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/query", tags=["RAG Query"])


@router.post(
    "/",
    response_model=QueryResponse,
    summary="Query your documents",
    description=(
        "Send a natural-language question. The system retrieves the most relevant chunks "
        "from your documents and generates a grounded answer via LangChain + OpenAI."
    ),
)
def query_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
):
    return rag_service.query(current_user.id, request.query, request.top_k)