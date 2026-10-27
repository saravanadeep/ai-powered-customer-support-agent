from pathlib import Path

from langchain_core.documents import Document

from app.services.rag_service import RAGService


def test_load_txt_document(tmp_path):

    file_path = tmp_path / "test.txt"

    file_path.write_text(
        "This is a customer support test document.",
        encoding="utf-8"
    )

    service = RAGService.__new__(
        RAGService
    )

    documents = service.load_document(
        str(file_path)
    )

    assert len(documents) == 1

    assert (
        "customer support"
        in documents[0].page_content.lower()
    )


def test_load_unsupported_document(tmp_path):

    file_path = tmp_path / "test.xyz"

    file_path.write_text(
        "Unsupported file"
    )

    service = RAGService.__new__(
        RAGService
    )

    try:

        service.load_document(
            str(file_path)
        )

        assert False, (
            "Expected ValueError "
            "was not raised."
        )

    except ValueError as e:

        assert "Unsupported file type" in str(e)


def test_search():

    service = RAGService.__new__(
        RAGService
    )

    class FakeRetriever:

        def invoke(self, query):

            return [
                Document(
                    page_content=(
                        "Refund policy information."
                    ),
                    metadata={
                        "source": "refund.txt"
                    }
                )
            ]

    service.retriever = FakeRetriever()

    results = service.search(
        "What is the refund policy?"
    )

    assert len(results) == 1

    assert (
        "Refund policy"
        in results[0].page_content
    )