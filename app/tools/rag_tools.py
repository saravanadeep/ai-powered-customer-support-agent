
from threading import Lock

from langchain_core.tools import tool

from app.config import RAG_BACKEND


# ==========================================
# RAG SERVICE INITIALIZATION
# ==========================================

_rag_service = None
_rag_service_lock = Lock()


def get_rag_service():

    global _rag_service

    if _rag_service is None:

        with _rag_service_lock:

            if _rag_service is None:

                if RAG_BACKEND == "chroma":

                    from app.services.rag_service import RAGService

                    _rag_service = RAGService()

                elif RAG_BACKEND == "tfidf":

                    from app.services.rag_tf_service import RAGTFService

                    _rag_service = RAGTFService()

                else:

                    raise ValueError(
                        f"Unsupported RAG_BACKEND: {RAG_BACKEND}"
                    )

    return _rag_service


# ==========================================
# KNOWLEDGE BASE TOOL
# ==========================================

@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the internal customer support knowledge base.

    Use this tool for:
    - Company policies
    - Customer support procedures
    - FAQs
    - Uploaded documents
    - Internal documentation
    """

    documents = get_rag_service().search(query)

    if not documents:

        return (
            "No relevant information found "
            "in the knowledge base."
        )

    results = []

    for i, document in enumerate(documents, start=1):

        source = document.metadata.get(
            "source",
            "Unknown source"
        )

        page = document.metadata.get("page")

        source_name = source.split("/")[-1]

        if page is not None:

            source_info = (
                f"{source_name}, page {page + 1}"
            )

        else:

            source_info = source_name

        results.append(
            f"""
SOURCE {i}
File: {source_info}

Content:
{document.page_content}
"""
        )

    return "\n".join(results)
