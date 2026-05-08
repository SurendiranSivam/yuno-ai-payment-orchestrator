"""
Workflow & Workflow Run API — manage workflows and trigger/view executions.
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col

from database import get_db
from models.workflow import Workflow
from models.workflow_run import WorkflowRun
from models.workflow_event import WorkflowEvent
from models.message import Message
from models.token_usage import TokenUsage

router = APIRouter(tags=["Workflows"])


# ── Schemas ───────────────────────────────────────────────

class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    graph_definition: dict = {}
    is_template: bool = False


class WorkflowRunTrigger(BaseModel):
    workflow_id: Optional[str] = None
    customer_message: str
    customer_phone: str = "manual-user"


# ── Workflow Endpoints ────────────────────────────────────

@router.get("/api/workflows")
async def list_workflows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).order_by(Workflow.created_at.desc()))
    return [_serialize_workflow(w) for w in result.scalars().all()]


@router.get("/api/workflows/templates")
async def list_workflow_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.is_template == True))
    return [_serialize_workflow(w) for w in result.scalars().all()]


@router.post("/api/workflows", status_code=201)
async def create_workflow(body: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    workflow = Workflow(**body.model_dump())
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    return _serialize_workflow(workflow)


# ── Workflow Run Endpoints ────────────────────────────────

@router.get("/api/workflow-runs")
async def list_workflow_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WorkflowRun).order_by(WorkflowRun.started_at.desc()).limit(limit)
    )
    return [_serialize_run(r) for r in result.scalars().all()]


@router.get("/api/workflow-runs/{run_id}")
async def get_workflow_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Get workflow run with its events, messages, and token usage."""
    stmt = select(WorkflowRun).where(WorkflowRun.id == run_id)
    run = (await db.execute(stmt)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    # Fetch related data
    events = (await db.execute(
        select(WorkflowEvent).where(WorkflowEvent.workflow_run_id == run_id).order_by(WorkflowEvent.created_at)
    )).scalars().all()

    messages = (await db.execute(
        select(Message).where(Message.workflow_run_id == run_id).order_by(Message.created_at)
    )).scalars().all()

    tokens = (await db.execute(
        select(TokenUsage).where(TokenUsage.workflow_run_id == run_id)
    )).scalars().all()

    result = _serialize_run(run)
    result["events"] = [_serialize_event(e) for e in events]
    result["messages"] = [_serialize_message(m) for m in messages]
    result["token_usage"] = [_serialize_token(t) for t in tokens]

    return result


@router.post("/api/workflow-runs", status_code=201)
async def trigger_workflow(body: WorkflowRunTrigger, background_tasks: BackgroundTasks):
    """Trigger a workflow execution asynchronously."""
    from runtime.orchestrator import orchestrator

    # Run the workflow in the background so the API returns immediately
    async def _run():
        await orchestrator.execute_workflow(
            customer_message=body.customer_message,
            customer_phone=body.customer_phone,
            workflow_id=body.workflow_id,
            trigger_source="api",
        )

    background_tasks.add_task(_run)

    return {
        "status": "accepted",
        "message": "Workflow execution started. Monitor via WebSocket or polling.",
    }


# ── Serializers ───────────────────────────────────────────

def _serialize_workflow(w: Workflow) -> dict:
    return {
        "id": str(w.id), "name": w.name, "description": w.description,
        "graph_definition": w.graph_definition, "is_template": w.is_template,
        "status": w.status, "created_at": w.created_at.isoformat() if w.created_at else None,
    }


def _serialize_run(r: WorkflowRun) -> dict:
    return {
        "id": str(r.id), "workflow_id": str(r.workflow_id), "status": r.status,
        "trigger_source": r.trigger_source, "input_data": r.input_data,
        "output_data": r.output_data,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
    }


def _serialize_event(e: WorkflowEvent) -> dict:
    return {
        "id": str(e.id), "agent_name": e.agent_name, "event_type": e.event_type,
        "message": e.message, "metadata": e.extra_data,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def _serialize_message(m: Message) -> dict:
    return {
        "id": str(m.id), "sender_agent": m.sender_agent, "receiver_agent": m.receiver_agent,
        "content": m.content, "metadata": m.extra_data,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _serialize_token(t: TokenUsage) -> dict:
    return {
        "id": str(t.id), "agent_name": t.agent_name,
        "prompt_tokens": t.prompt_tokens, "completion_tokens": t.completion_tokens,
        "total_tokens": t.total_tokens, "model": t.model,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }
