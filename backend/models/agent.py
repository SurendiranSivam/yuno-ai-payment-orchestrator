"""Agent model — represents a configurable AI agent in the orchestration platform."""

import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import SQLModel, Field


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    name: str = Field(max_length=100, index=True)
    role: str = Field(max_length=50)  # e.g. customer_support, fraud_detection
    system_prompt: str = Field(default="")
    model: str = Field(default="gpt-4o", max_length=50)

    # JSON config: tools, guardrails, channels, schedules, interaction_rules
    config: dict = Field(default_factory=dict, sa_column=sa.Column(sa.JSON, default={}))

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

