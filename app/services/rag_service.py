from pathlib import Path
from threading import Lock


from app.config import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL
)

from app.logging_config import get_logger


class RAGService:

    logger = get_logger(__name__)

    def __init__(self):
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings

        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL
        )

        self.vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PATH
        )

        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 4}
        )

        self.logger.info(
            "RAGService initialized successfully."
        )

    def load_document(self, file_path: str):

        from langchain_community.document_loaders import (
                    PyPDFLoader,
                    TextLoader,
                    Docx2txtLoader
                )

        path = Path(file_path)
        extension = path.suffix.lower()

        self.logger.info(
            f"Loading document. file={path.name}, "
            f"type={extension}"
        )

        if extension == ".pdf":

            loader = PyPDFLoader(
                str(path)
            )

        elif extension == ".txt":

            loader = TextLoader(
                str(path),
                encoding="utf-8"
            )

        elif extension == ".docx":

            loader = Docx2txtLoader(
                str(path)
            )

        else:

            self.logger.warning(
                f"Unsupported document type: {extension}"
            )

            raise ValueError(
                "Unsupported file type. "
                "Only PDF, TXT and DOCX files are supported."
            )

        documents = loader.load()

        self.logger.info(
            f"Document loaded successfully. "
            f"file={path.name}, documents={len(documents)}"
        )

        return documents

    def load_documents(self, documents_path="documents"):
       

        documents = []

        folder = Path(documents_path)

        for file in folder.iterdir():

            if file.suffix.lower() in {
                ".pdf",
                ".txt",
                ".docx"
            }:

                documents.extend(
                    self.load_document(
                        str(file)
                    )
                )

        self.logger.info(
            f"Documents loaded from folder. "
            f"folder={documents_path}, "
            f"documents={len(documents)}"
        )

        return documents

    def create_vectorstore(self, documents_path="documents"):

        from langchain_text_splitters import RecursiveCharacterTextSplitter


        documents = self.load_documents(
            documents_path
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100
        )

        chunks = splitter.split_documents(
            documents
        )

        self.vectorstore.add_documents(
            chunks
        )

        self.logger.info(
            f"Vector store created/updated. "
            f"documents={len(documents)}, "
            f"chunks={len(chunks)}"
        )

        return len(chunks)

    def add_document(self, file_path: str):

        from langchain_text_splitters import RecursiveCharacterTextSplitter


        path = Path(file_path)

        try:

            documents = self.load_document(
                file_path
            )

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=700,
                chunk_overlap=100
            )

            chunks = splitter.split_documents(
                documents
            )

            if not chunks:

                self.logger.warning(
                    f"No readable content found. "
                    f"file={path.name}"
                )

                return {
                    "success": False,
                    "message": (
                        "No readable content found "
                        "in the document."
                    ),
                    "chunks": 0
                }

            self.vectorstore.add_documents(
                chunks
            )

            self.logger.info(
                f"Document indexed successfully. "
                f"file={path.name}, "
                f"chunks={len(chunks)}"
            )

            return {
                "success": True,
                "message": "Document successfully indexed.",
                "filename": path.name,
                "chunks": len(chunks)
            }

        except Exception:

            self.logger.exception(
                f"Failed to index document. "
                f"file={path.name}"
            )

            raise

    def search(self, query: str):

        self.logger.info(
            f"Knowledge base search started. "
            f"query='{query}'"
        )

        try:

            documents = self.retriever.invoke(
                query
            )

            self.logger.info(
                f"Knowledge base search completed. "
                f"results={len(documents)}"
            )

            return documents

        except Exception:

            self.logger.exception(
                "Knowledge base search failed."
            )

            raise


_rag_service = None
_rag_service_lock = Lock()


def get_rag_service():
    global _rag_service

    if _rag_service is None:
        with _rag_service_lock:
            if _rag_service is None:
                _rag_service = RAGService()

    return _rag_service
