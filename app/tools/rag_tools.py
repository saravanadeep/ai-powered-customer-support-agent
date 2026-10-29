from langchain_core.tools import tool

from app.services.rag_service import RAGService


rag_service = RAGService()


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the internal customer support knowledge base.

    Use this tool for questions about:
    - company policies
    - customer support procedures
    - FAQs
    - uploaded documents
    - internal documentation
    """

    documents = rag_service.search(query)

    if not documents:
        return "No relevant information found in the knowledge base."

    results = []

    for i, document in enumerate(documents, start=1):

        source = document.metadata.get(
            "source",
            "Unknown source"
        )

        page = document.metadata.get("page")

        source_name = source.split("/")[-1]

        if page is not None:
            source_info = f"{source_name}, page {page + 1}"
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