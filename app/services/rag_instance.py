
from functools import lru_cache

from app.services.rag_service import RAGService


@lru_cache(maxsize=1)
def get_rag_service():
    """Create one shared RAG service per Python process."""
    return RAGService()
