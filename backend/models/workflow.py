"""Workflow model — defines orchestration workflows and prebuilt templates."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import SQLModel, Field


class Workflow(SQLModel, table=True):
    __tablename__ = "workflows"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    name: str = Field(max_length=100, index=True)
    description: str = Field(default="")

    # Node/edge definitions for React Flow visualization
    graph_definition: dict = Field(default_factory=dict, sa_column=sa.Column(sa.JSON, default={}))

    is_template: bool = Field(default=False)
    status: str = Field(default="active", max_length=20)  # active / archived
    created_at: datetime = Field(default_factory=datetime.utcnow)

