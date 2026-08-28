from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class ChatQueryRequest(BaseModel):
    message: str = Field(..., description="The user's question or prompt")
    conversation_id: Optional[int] = Field(None, description="Conversation ID to continue, or null to start new")


class FeedbackCreateRequest(BaseModel):
    message_id: int
    rating: int = Field(..., description="1 for Helpful/Positive, -1 for Not Helpful/Negative")
    feedback: Optional[str] = Field(None, description="Optional text feedback explaining the rating")


class FeedbackResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    rating: int
    feedback: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    sources: Optional[List[Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class ConversationUpdateTitle(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
