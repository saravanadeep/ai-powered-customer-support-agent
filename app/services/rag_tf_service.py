
import os
import threading
from pathlib import Path

import joblib
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader
)

from app.logging_config import get_logger


class RAGTFService:

    logger = get_logger(__name__)

    def __init__(
        self,
        index_path="./tfidf_index/tfidf_index.joblib"
    ):
        self.remote_sync = (
            os.getenv("TFIDF_REMOTE_SYNC", "false").lower() == "true"
        )

        self.remote_index_key = "indexes/tfidf_index.joblib"
        self.index_path = Path(index_path)

        self.index_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.lock = threading.RLock()

        self.vectorizer = self._create_vectorizer()
        self.documents = []
        self.tfidf_matrix = None

        # Strict startup: remote index must be available and valid
        # whenever remote synchronization is enabled.
        if self.remote_sync:
            self.download_remote_index()

        self.load_index()

        self.logger.info(
            "RAGTFService initialized successfully."
        )

    # ==========================================
    # CREATE VECTORIZER
    # ==========================================

    @staticmethod
    def _create_vectorizer():
        return TfidfVectorizer(
            max_features=50000,
            ngram_range=(1, 1),
            sublinear_tf=True,
            dtype=np.float32
        )

    # ==========================================
    # VALIDATE INDEX DATA
    # ==========================================

    @staticmethod
    def _validate_index_data(data):

        if not isinstance(data, dict):
            raise ValueError("Invalid TF-IDF index format.")

        required_keys = {
            "documents",
            "vectorizer",
            "tfidf_matrix"
        }

        if not required_keys.issubset(data):
            raise ValueError(
                "TF-IDF index is missing required fields."
            )

        documents = data["documents"]
        vectorizer = data["vectorizer"]
        matrix = data["tfidf_matrix"]

        if not isinstance(documents, list):
            raise ValueError("Invalid documents collection.")

        for item in documents:
            if not isinstance(item, dict):
                raise ValueError("Invalid document entry.")

            if not isinstance(item.get("page_content"), str):
                raise ValueError("Invalid document content.")

            if not isinstance(item.get("metadata"), dict):
                raise ValueError("Invalid document metadata.")

        if not hasattr(vectorizer, "transform"):
            raise ValueError("Invalid TF-IDF vectorizer.")

        if documents:
            if matrix is None or not hasattr(matrix, "shape"):
                raise ValueError("TF-IDF matrix is missing.")

            if matrix.shape[0] != len(documents):
                raise ValueError(
                    "Document count and TF-IDF matrix rows do not match."
                )

            if matrix.shape[1] != len(vectorizer.get_feature_names_out()):
                raise ValueError(
                    "Vectorizer and TF-IDF matrix dimensions do not match."
                )

        elif matrix is not None and matrix.shape[0] != 0:
            raise ValueError(
                "Empty document collection has a non-empty matrix."
            )

        return True

    # ==========================================
    # DOWNLOAD REMOTE INDEX
    # ==========================================

    def download_remote_index(self):
        """
        Strict remote startup.

        When remote sync is enabled:
        - Remote index must exist.
        - Download must succeed.
        - Downloaded index must pass validation.
        - Local index is replaced only after validation.
        """

        if not self.remote_sync:
            self.logger.info("Remote TF-IDF sync disabled.")
            return

        from app.services.storage_service import download_index_file

        temp_path = self.index_path.with_name(
            self.index_path.name + ".download"
        )

        try:
            self.logger.info(
                "Downloading remote TF-IDF index..."
            )

            result = download_index_file(
                self.remote_index_key,
                str(temp_path)
            )

            if not result.get("success"):
                raise RuntimeError(
                    "Remote TF-IDF index is missing. "
                    "Strict startup cannot continue."
                )

            if not temp_path.exists() or temp_path.stat().st_size == 0:
                raise RuntimeError(
                    "Downloaded TF-IDF index is empty or missing."
                )

            # Only load trusted index files from your own storage.
            downloaded_data = joblib.load(temp_path)

            self._validate_index_data(downloaded_data)

            # Replace local index only after successful validation.
            os.replace(
                temp_path,
                self.index_path
            )

            self.logger.info(
                "Remote TF-IDF index downloaded and validated successfully."
            )

        except Exception as exc:

            self.logger.exception(
                "Strict remote TF-IDF startup failed."
            )

            raise RuntimeError(
                "Could not download or validate the remote TF-IDF index. "
                "Application startup aborted."
            ) from exc

        finally:
            if temp_path.exists():
                temp_path.unlink()

    # ==========================================
    # LOAD SAVED INDEX
    # ==========================================

    def load_index(self):

        if not self.index_path.exists():

            if self.remote_sync:
                raise RuntimeError(
                    "Remote synchronization is enabled, "
                    "but no validated local index is available."
                )

            self.logger.info(
                "No existing TF-IDF index found."
            )
            return

        try:

            # Only load index files generated by this application.
            data = joblib.load(self.index_path)

            self._validate_index_data(data)

            loaded_documents = [
                Document(
                    page_content=item["page_content"],
                    metadata=item["metadata"]
                )
                for item in data["documents"]
            ]

            # Update state only after complete validation.
            self.documents = loaded_documents
            self.vectorizer = data["vectorizer"]
            self.tfidf_matrix = data["tfidf_matrix"]

            self.logger.info(
                f"TF-IDF index loaded. "
                f"documents={len(self.documents)}"
            )

        except Exception as exc:

            self.logger.exception(
                "Failed to load TF-IDF index."
            )

            raise RuntimeError(
                "Could not load the saved TF-IDF index. "
                "Check the index file before continuing."
            ) from exc

    # ==========================================
    # UPLOAD REMOTE INDEX
    # ==========================================

    def upload_remote_index(self, file_path=None):
        """Upload a candidate or existing index to remote storage."""

        if not self.remote_sync:
            return

        from app.services.storage_service import upload_index_file

        upload_path = (
            Path(file_path)
            if file_path is not None
            else self.index_path
        )

        if not upload_path.exists():
            raise FileNotFoundError(
                f"TF-IDF index does not exist: {upload_path}"
            )

        result = upload_index_file(
            str(upload_path),
            self.remote_index_key
        )

        if not result.get("success"):
            raise RuntimeError(
                "Failed to upload TF-IDF index to object storage."
            )

        self.logger.info(
            "Remote TF-IDF index uploaded successfully."
        )

    # ==========================================
    # SAVE INDEX TRANSACTIONALLY
    # ==========================================

    def save_index(
        self,
        documents=None,
        vectorizer=None,
        tfidf_matrix=None
    ):
        """
        Save a candidate index.

        Order:
        1. Serialize candidate to temporary file.
        2. Upload candidate to remote storage, if enabled.
        3. Replace local index atomically.

        In-memory state is updated by build_index only after this succeeds.
        """

        candidate_documents = (
            self.documents if documents is None else documents
        )

        candidate_vectorizer = (
            self.vectorizer if vectorizer is None else vectorizer
        )

        candidate_matrix = (
            self.tfidf_matrix if tfidf_matrix is None else tfidf_matrix
        )

        temporary_path = self.index_path.with_name(
            self.index_path.name + ".tmp"
        )

        data = {
            "documents": [
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in candidate_documents
            ],
            "vectorizer": candidate_vectorizer,
            "tfidf_matrix": candidate_matrix
        }

        self._validate_index_data(data)

        try:

            joblib.dump(
                data,
                temporary_path,
                compress=3
            )

            if (
                not temporary_path.exists()
                or temporary_path.stat().st_size == 0
            ):
                raise RuntimeError(
                    "Temporary TF-IDF index was not created correctly."
                )

            # Verify that the serialized candidate can be loaded.
            verification_data = joblib.load(temporary_path)
            self._validate_index_data(verification_data)

            # Remote first: a failed upload leaves the old local
            # index and in-memory state untouched.
            if self.remote_sync:
                self.upload_remote_index(temporary_path)

            # Atomic local replacement.
            os.replace(
                temporary_path,
                self.index_path
            )

            self.logger.info(
                "TF-IDF index saved successfully."
            )

        finally:

            if temporary_path.exists():
                temporary_path.unlink()

    # ==========================================
    # LOAD DOCUMENT
    # ==========================================

    def load_document(self, file_path: str):

        path = Path(file_path)

        extension = path.suffix.lower()

        if extension == ".pdf":

            loader = PyPDFLoader(str(path))

        elif extension == ".txt":

            loader = TextLoader(
                str(path),
                encoding="utf-8"
            )

        elif extension == ".docx":

            loader = Docx2txtLoader(str(path))

        else:

            raise ValueError(
                "Only PDF, TXT and DOCX files are supported."
            )

        documents = list(loader.lazy_load())

        self.logger.info(
            f"Document loaded. "
            f"file={path.name}, "
            f"pages={len(documents)}"
        )

        return documents

    # ==========================================
    # BUILD TF-IDF INDEX
    # ==========================================

    def build_index(self, documents=None):

        with self.lock:

            candidate_documents = (
                list(self.documents)
                if documents is None
                else list(documents)
            )

            if not candidate_documents:

                candidate_vectorizer = self._create_vectorizer()
                candidate_matrix = None

            else:

                texts = [
                    document.page_content
                    for document in candidate_documents
                ]

                candidate_vectorizer = self._create_vectorizer()

                candidate_vectorizer.fit(texts)

                candidate_matrix = (
                    candidate_vectorizer.transform(texts)
                )

            # Persist before changing active in-memory state.
            self.save_index(
                documents=candidate_documents,
                vectorizer=candidate_vectorizer,
                tfidf_matrix=candidate_matrix
            )

            self.documents = candidate_documents
            self.vectorizer = candidate_vectorizer
            self.tfidf_matrix = candidate_matrix

            self.logger.info(
                f"TF-IDF index built. "
                f"chunks={len(self.documents)}"
            )

            return len(self.documents)

    # ==========================================
    # ADD DOCUMENT
    # ==========================================

    def add_document(self, file_path: str):

        path = Path(file_path)

        try:

            documents = self.load_document(file_path)

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=700,
                chunk_overlap=100
            )

            chunks = splitter.split_documents(
                documents
            )

            if not chunks:

                return {
                    "success": False,
                    "message": "No readable content found.",
                    "chunks": 0
                }

            with self.lock:

                candidate_documents = (
                    list(self.documents) + chunks
                )

                # build_index commits state only after successful
                # local persistence and remote upload.
                self.build_index(candidate_documents)

            self.logger.info(
                f"TF-IDF document indexed. "
                f"file={path.name}, "
                f"chunks={len(chunks)}"
            )

            return {
                "success": True,
                "message": "Document indexed successfully using TF-IDF.",
                "filename": path.name,
                "chunks": len(chunks)
            }

        except Exception:

            self.logger.exception(
                f"TF-IDF indexing failed. file={path.name}"
            )

            raise

    # ==========================================
    # SEARCH KNOWLEDGE BASE
    # ==========================================

    def search(self, query: str, k: int = 4):

        if not query or not query.strip() or k <= 0:
            return []

        with self.lock:

            if (
                not self.documents
                or self.tfidf_matrix is None
            ):
                return []

            query_vector = self.vectorizer.transform(
                [query]
            )

            similarities = (
                self.tfidf_matrix @ query_vector.T
            ).toarray().ravel()

            if not np.any(similarities > 0):
                return []

            top_indices = np.argsort(
                similarities
            )[::-1][:k]

            results = []

            for index in top_indices:

                if similarities[index] <= 0:
                    continue

                results.append(
                    self.documents[index]
                )

            self.logger.info(
                f"TF-IDF search completed. "
                f"results={len(results)}"
            )

            return results
