
from pathlib import Path

# Only approved customer-support documents
DOCUMENTS = [
    {
        "filename": "account_policy.pdf",
        "path": "documents/account_policy.pdf",
        "source": "documents/account_policy.pdf",
        "content_type": "application/pdf",
    },
    {
        "filename": "shipping_policy.pdf",
        "path": "documents/shipping_policy.pdf",
        "source": "documents/shipping_policy.pdf",
        "content_type": "application/pdf",
    },
    {
        "filename": "refund_policy.pdf",
        "path": "documents/refund_policy.pdf",
        "source": "documents/refund_policy.pdf",
        "content_type": "application/pdf",
    },
    {
        "filename": "product_manual.pdf",
        "path": "documents/product_manual.pdf",
        "source": "documents/product_manual.pdf",
        "content_type": "application/pdf",
    },
    {
        "filename": "support_guidelines.txt",
        "path": "documents/support_guidelines.txt",
        "source": "documents/support_guidelines.txt",
        "content_type": "text/plain",
    },
    {
        "filename": "faq.txt",
        "path": "documents/faq.txt",
        "source": "documents/faq.txt",
        "content_type": "text/plain",
    },
]


def validate_documents():
    """Verify that all approved source files exist locally."""

    missing = []

    for document in DOCUMENTS:
        path = Path(document["path"])

        if not path.is_file():
            missing.append(str(path))

    if missing:
        raise FileNotFoundError(
            f"Missing knowledge-base documents: {missing}"
        )

    print(f"Validated {len(DOCUMENTS)} documents.")

    for document in DOCUMENTS:
        print("-", document["filename"])


if __name__ == "__main__":
    validate_documents()
