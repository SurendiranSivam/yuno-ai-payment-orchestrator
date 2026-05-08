"""WorkflowEvent model — observability log for agent execution steps."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import SQLModel, Field


class WorkflowEvent(SQLModel, table=True):
    __tablename__ = "workflow_events"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    workflow_run_id: str = Field(index=True)
    agent_name: str = Field(max_length=100)
    event_type: str = Field(max_length=50)  # node_start / node_complete / error / decision
    message: str = Field(default="")
    extra_data: dict = Field(default_factory=dict, sa_column=sa.Column("metadata", sa.JSON, default={}))
    created_at: datetime = Field(default_factory=datetime.utcnow)

