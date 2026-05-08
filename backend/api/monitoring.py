"""
Monitoring API — dashboard stats, recent events, and activity feed.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from database import get_db
from models.agent import Agent
from models.workflow import Workflow
from models.workflow_run import WorkflowRun
from models.workflow_event import WorkflowEvent
from models.conversation import Conversation
from models.token_usage import TokenUsage

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate stats for the dashboard overview."""
    total_agents = (await db.execute(select(func.count(Agent.id)))).scalar() or 0
    total_workflows = (await db.execute(select(func.count(Workflow.id)))).scalar() or 0
    total_runs = (await db.execute(select(func.count(WorkflowRun.id)))).scalar() or 0
    active_runs = (await db.execute(
        select(func.count(WorkflowRun.id)).where(WorkflowRun.status == "running")
    )).scalar() or 0
    completed_runs = (await db.execute(
        select(func.count(WorkflowRun.id)).where(WorkflowRun.status == "completed")
    )).scalar() or 0
    failed_runs = (await db.execute(
        select(func.count(WorkflowRun.id)).where(WorkflowRun.status == "failed")
    )).scalar() or 0
    total_conversations = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0

    # Token usage aggregates
    total_tokens = (await db.execute(select(func.sum(TokenUsage.total_tokens)))).scalar() or 0

    return {
        "total_agents": total_agents,
        "total_workflows": total_workflows,
        "total_runs": total_runs,
        "active_runs": active_runs,
        "completed_runs": completed_runs,
        "failed_runs": failed_runs,
        "total_conversations": total_conversations,
        "total_tokens_used": total_tokens,
    }


@router.get("/events")
async def get_recent_events(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Fetch recent workflow events for the activity feed."""
    result = await db.execute(
        select(WorkflowEvent).order_by(WorkflowEvent.created_at.desc()).limit(limit)
    )
    events = result.scalars().all()

    return [{
        "id": str(e.id),
        "workflow_run_id": str(e.workflow_run_id),
        "agent_name": e.agent_name,
        "event_type": e.event_type,
        "message": e.message,
        "metadata": e.extra_data,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    } for e in events]
