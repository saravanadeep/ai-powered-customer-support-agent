
from app.services.rag_tf_service import RAGTFService

# Initialize service and load saved index
rag = RAGTFService()

print("\nTesting saved index...")

queries = [
    "What is the refund period?",
    "How long does a refund take?",
    "Which products are not eligible for refunds?"
]

for query in queries:

    print("\nQUESTION:", query)

    results = rag.search(query)

    for document in results:
        print("RESULT:", document.page_content)
