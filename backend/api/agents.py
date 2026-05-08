"""
Agent CRUD API — create, read, update, delete AI agents.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from database import get_db
from models.agent import Agent

router = APIRouter(prefix="/api/agents", tags=["Agents"])


# ── Request/Response Schemas ──────────────────────────────

class AgentCreate(BaseModel):
    name: str
    role: str
    system_prompt: str = ""
    model: str = "gpt-4o"
    config: dict = {}
    is_active: bool = True


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


# ── Endpoints ─────────────────────────────────────────────

@router.get("")
async def list_agents(db: AsyncSession = Depends(get_db)):
    """List all configured agents."""
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    agents = result.scalars().all()
    return [_serialize_agent(a) for a in agents]


@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single agent by ID."""
    agent = await _get_agent_or_404(agent_id, db)
    return _serialize_agent(agent)


@router.post("", status_code=201)
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new agent."""
    agent = Agent(**body.model_dump())
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return _serialize_agent(agent)


@router.put("/{agent_id}")
async def update_agent(agent_id: str, body: AgentUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing agent."""
    agent = await _get_agent_or_404(agent_id, db)
    update_data = body.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(agent, field, value)

    agent.updated_at = datetime.utcnow()
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return _serialize_agent(agent)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an agent."""
    agent = await _get_agent_or_404(agent_id, db)
    await db.delete(agent)


# ── Helpers ───────────────────────────────────────────────

async def _get_agent_or_404(agent_id: str, db: AsyncSession) -> Agent:
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


def _serialize_agent(agent: Agent) -> dict:
    return {
        "id": str(agent.id),
        "name": agent.name,
        "role": agent.role,
        "system_prompt": agent.system_prompt,
        "model": agent.model,
        "config": agent.config,
        "is_active": agent.is_active,
        "created_at": agent.created_at.isoformat() if agent.created_at else None,
        "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
    }
