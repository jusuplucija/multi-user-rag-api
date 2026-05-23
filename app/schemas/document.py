from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    filename: str
    content_type: str
    created_at: datetime


class DocumentSortBy(str, Enum):
    filename = "filename"
    created_at = "created_at"
    content_type = "content_type"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class PaginatedDocumentsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[DocumentResponse]


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceReference(BaseModel):
    filename: str
    page: int | None = None  # 1-indexed; None for plain-text files which have no pages


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceReference]