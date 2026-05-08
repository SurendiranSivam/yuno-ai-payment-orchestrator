"""WorkflowRun model — tracks individual executions of a workflow."""

import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import SQLModel, Field


class WorkflowRun(SQLModel, table=True):
    __tablename__ = "workflow_runs"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    workflow_id: str = Field(index=True)
    status: str = Field(default="pending", max_length=20)  # pending / running / completed / failed
    trigger_source: str = Field(default="manual", max_length=20)  # whatsapp / api / manual

    # Request/response payloads
    input_data: dict = Field(default_factory=dict, sa_column=sa.Column(sa.JSON, default={}))
    output_data: dict = Field(default_factory=dict, sa_column=sa.Column(sa.JSON, default={}))

    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

