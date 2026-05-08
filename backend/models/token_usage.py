"""TokenUsage model — tracks LLM token consumption per agent per workflow run."""

import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field


class TokenUsage(SQLModel, table=True):
    __tablename__ = "token_usage"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    workflow_run_id: str = Field(index=True)
    agent_name: str = Field(max_length=100)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    model: str = Field(default="gpt-4o", max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)

