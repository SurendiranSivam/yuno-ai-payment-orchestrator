"""
Conversations API — WhatsApp message history.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from database import get_db
from models.conversation import Conversation

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get("")
async def list_conversations(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """List recent conversations grouped by phone number."""
    result = await db.execute(
        select(Conversation).order_by(Conversation.created_at.desc()).limit(limit)
    )
    conversations = result.scalars().all()

    return [{
        "id": str(c.id),
        "workflow_run_id": str(c.workflow_run_id) if c.workflow_run_id else None,
        "user_phone": c.user_phone,
        "direction": c.direction,
        "message": c.message,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c in conversations]
