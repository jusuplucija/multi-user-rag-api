from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.vector_store import vector_store_service

_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question using only the provided context. "
    "If the answer cannot be found in the context, say so clearly."
)


class RAGService:
    """Retrieves relevant document chunks and generates answers via LangChain.

    LLM priority:
      1. OpenAI (gpt-3.5-turbo) — used when OPENAI_API_KEY is set.
      2. Ollama (local)          — used otherwise; requires the Ollama service to be running.
    If neither is reachable the raw retrieved context is returned instead.
    """

    def _build_llm(self):
        if settings.openai_api_key:
            return ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-3.5-turbo",
                temperature=0,
            )
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0,
        )

    def query(self, user_id: int, query: str, top_k: int = 5) -> dict:
        results = vector_store_service.search(user_id, query, top_k)

        if not results:
            return {
                "query": query,
                "answer": "No documents found. Please upload documents before querying.",
                "sources": [],
            }

        context = "\n\n---\n\n".join(r["content"] for r in results)
        sources = sorted({r["metadata"]["filename"] for r in results})

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}"),
        ]

        try:
            llm = self._build_llm()
            response = llm.invoke(messages)
            return {
                "query": query,
                "answer": response.content,
                "sources": sources,
            }
        except Exception as exc:
            return {
                "query": query,
                "answer": (
                    f"LLM unavailable ({exc}).\n\n"
                    f"Retrieved context:\n\n{context}"
                ),
                "sources": sources,
            }


rag_service = RAGService()