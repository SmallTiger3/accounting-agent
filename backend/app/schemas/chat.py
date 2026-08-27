from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class ChatMessageCreate(BaseModel):
    content: str
    session_id: Optional[int] = None  # None for new session


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    tool_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None
    last_message: Optional[str] = None

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    session_id: int
    message: ChatMessageResponse
    budget_alerts: Optional[List[str]] = None
