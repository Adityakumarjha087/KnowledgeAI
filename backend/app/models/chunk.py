import json
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text, Integer, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin
from app.core.config import settings

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.user import User


class SafeVector(TypeDecorator):
    """
    A custom SQLAlchemy type that compiles to the native pgvector Vector type 
    on PostgreSQL, and falls back to a serialized JSON Text column in SQLite 
    for local unit-testing purposes.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        else:
            return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # For SQLite fallback: serialize list of floats to JSON string
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            # pgvector library returns numpy arrays or lists depending on settings,
            # but usually lists or floats directly. We pass it through.
            return value
        # For SQLite fallback: deserialize string back into list of floats
        return json.loads(value)


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=True)
    section: Mapped[str] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Store high-dimensional embeddings. Use SafeVector to fallback on SQLite.
    embedding: Mapped[list] = mapped_column(
        SafeVector(settings.EMBEDDING_DIMENSION), 
        nullable=True
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
