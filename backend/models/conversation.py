"""Conversation model — WhatsApp message history (inbound + outbound)."""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    workflow_run_id: Optional[str] = Field(default=None, index=True)
    user_phone: str = Field(max_length=20, index=True)
    direction: str = Field(max_length=10)  # inbound / outbound
    message: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)

