from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Float, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class QueryLog(Base, TimestampMixin):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), 
        index=True, 
        nullable=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Store chunk reference details returned during hybrid search context selection
    # Structured as: [{"chunk_id": int, "document_id": int, "score": float}]
    retrieved_chunks: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Latency tracking (in seconds)
    retrieval_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    llm_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Cost & Usage metrics
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Error logging
    errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
