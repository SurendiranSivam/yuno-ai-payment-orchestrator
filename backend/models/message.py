"""Message model — inter-agent messages exchanged during workflow execution."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import SQLModel, Field


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    workflow_run_id: str = Field(index=True)
    sender_agent: str = Field(max_length=100)
    receiver_agent: str = Field(max_length=100)
    content: str = Field(default="")
    extra_data: dict = Field(default_factory=dict, sa_column=sa.Column("metadata", sa.JSON, default={}))
    created_at: datetime = Field(default_factory=datetime.utcnow)

