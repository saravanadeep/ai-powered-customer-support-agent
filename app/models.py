from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    Index
)

from pgvector.sqlalchemy import Vector
from app.database import Base

class Customer(Base):

    __tablename__ = "customers"

    customer_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False
    )

    phone = Column(String(20))

    company = Column(String(100))

    status = Column(
        String(30),
        default="Active"
    )

    plan = Column(
        String(30),
        default="Basic"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Ticket(Base):

    __tablename__ = "tickets"

    ticket_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.customer_id"),
        nullable=False
    )

    issue = Column(
        Text,
        nullable=False
    )

    priority = Column(
        String(20),
        default="Medium"
    )

    status = Column(
        String(30),
        default="Open"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class User(Base):

    __tablename__ = "users"

    user_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(30),
        nullable=False,
        default="Support Agent"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

class KnowledgeDocument(Base):

    __tablename__ = "knowledge_documents"

    document_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    filename = Column(
        String(255),
        nullable=False
    )

    storage_key = Column(
        String(500),
        nullable=False,
        unique=True
    )

    file_type = Column(
        String(20),
        nullable=False
    )

    checksum = Column(
        String(64),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


class KnowledgeChunk(Base):

    __tablename__ = "knowledge_chunks"

    chunk_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Original ChromaDB record ID
    chroma_id = Column(
        String(36),
        nullable=False,
        unique=True
    )

    document_id = Column(
        Integer,
        ForeignKey(
            "knowledge_documents.document_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    chunk_text = Column(
        Text,
        nullable=False
    )

    source_metadata = Column(
        Text,
        nullable=True
    )

    embedding = Column(
        Vector(384),
        nullable=False
    )

    __table_args__ = (
        Index(
            "ix_knowledge_chunks_document_id",
            "document_id"
        ),
    )



