"""
WhatsApp Webhook API — handles Meta webhook verification and incoming messages.

GET  /api/whatsapp/webhook  → verification handshake
POST /api/whatsapp/webhook  → incoming message processing
POST /api/whatsapp/simulate → simulate a WhatsApp message (for demo without Meta credentials)
"""

import asyncio

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

from config import get_settings
from messaging.whatsapp_client import whatsapp_client, WhatsAppClient
from database import async_session
from models.conversation import Conversation

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])
settings = get_settings()


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Handle Meta webhook verification handshake."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return int(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Process incoming WhatsApp messages and trigger orchestration workflow."""
    payload = await request.json()
    extracted = WhatsAppClient.extract_message_from_payload(payload)

    if not extracted:
        return {"status": "ok"}  # Acknowledge non-message events

    phone = extracted["phone"]
    message_text = extracted["message"]

    # Trigger orchestration workflow in background
    async def _process():
        from runtime.orchestrator import orchestrator

        result = await orchestrator.execute_workflow(
            customer_message=message_text,
            customer_phone=phone,
            trigger_source="whatsapp",
        )

        # Send WhatsApp reply if we have credentials and got a response
        final_response = result.get("final_response", "")
        if final_response and settings.whatsapp_token:
            await whatsapp_client.send_text_message(to=phone, body=final_response)

        # Persist outbound conversation
        if final_response:
            async with async_session() as session:
                session.add(Conversation(
                    workflow_run_id=result.get("workflow_run_id"),
                    user_phone=phone,
                    direction="outbound",
                    message=final_response,
                ))
                await session.commit()

    background_tasks.add_task(_process)
    return {"status": "ok"}


# ── Simulation endpoint for demo without Meta credentials ─

class SimulateMessage(BaseModel):
    phone: str = "+1234567890"
    message: str


@router.post("/simulate")
async def simulate_whatsapp_message(body: SimulateMessage, background_tasks: BackgroundTasks):
    """Simulate a WhatsApp message for demo purposes — triggers the full orchestration pipeline."""
    from runtime.orchestrator import orchestrator

    async def _process():
        result = await orchestrator.execute_workflow(
            customer_message=body.message,
            customer_phone=body.phone,
            trigger_source="whatsapp",
        )

        # Persist outbound conversation
        final_response = result.get("final_response", "")
        if final_response:
            async with async_session() as session:
                session.add(Conversation(
                    workflow_run_id=result.get("workflow_run_id"),
                    user_phone=body.phone,
                    direction="outbound",
                    message=final_response,
                ))
                await session.commit()

    background_tasks.add_task(_process)

    return {
        "status": "accepted",
        "message": f"Simulated WhatsApp message from {body.phone}. Monitor execution on the dashboard.",
    }
