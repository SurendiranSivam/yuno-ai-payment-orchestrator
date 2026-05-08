"""
Base utilities for agent nodes — shared LLM calling, event persistence, and message logging.

All agent nodes use these helpers to:
1. Call OpenAI with their system prompt
2. Persist workflow events for realtime monitoring
3. Record inter-agent messages
4. Track token usage
"""

import json
import uuid
from datetime import datetime

from config import get_settings
from realtime.connection_manager import ws_manager

settings = get_settings()

# ── LLM Fallback ─────────────────────────────────────────────
# When OPENAI_API_KEY is not set, use intelligent mock responses
# so the orchestration demo works without external API dependencies.


async def call_llm(
    system_prompt: str,
    user_message: str,
    agent_name: str,
    workflow_run_id: str,
) -> tuple[str, dict]:
    """
    Call OpenAI or return a mock response if API key is not configured.
    Returns (response_text, token_info_dict).
    """
    token_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model": settings.default_model}

    if settings.openai_api_key:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=1024,
            )

            result = response.choices[0].message.content
            usage = response.usage
            token_info = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "model": settings.default_model,
            }

            # Persist token usage
            await _persist_token_usage(workflow_run_id, agent_name, token_info)

            return result, token_info

        except Exception as e:
            # Fall through to mock if API call fails
            await persist_event(
                workflow_run_id=workflow_run_id,
                agent_name=agent_name,
                event_type="warning",
                message=f"LLM call failed, using mock response: {str(e)[:100]}",
            )

    # Mock response mode — generate realistic domain-specific responses
    mock_result = _get_mock_response(agent_name, user_message)
    token_info = {"prompt_tokens": 150, "completion_tokens": 200, "total_tokens": 350, "model": "mock-gpt-4o"}

    await _persist_token_usage(workflow_run_id, agent_name, token_info)
    return mock_result, token_info


def _get_mock_response(agent_name: str, user_message: str) -> str:
    """Generate realistic mock responses for demo mode."""
    mocks = {
        "CustomerSupportAgent": json.dumps({
            "intent": "payment_failure",
            "category": "payment",
            "extracted_details": {
                "issue_summary": "Payment failed but amount was deducted from customer account",
                "mentioned_amount": "$49.99",
                "transaction_reference": "TXN-2024-78432",
                "payment_method": "card",
                "urgency": "high",
            },
            "sentiment": "frustrated",
            "initial_response": "I understand your frustration. Your payment issue is being investigated by our team right now.",
        }),
        "FraudDetectionAgent": json.dumps({
            "risk_score": 0.15,
            "risk_level": "low",
            "flags": [],
            "analysis": "No suspicious patterns detected. Transaction appears legitimate.",
            "recommendation": "proceed_with_verification",
            "checked_patterns": ["velocity_check", "geo_anomaly", "amount_deviation", "device_fingerprint"],
        }),
        "PaymentVerificationAgent": json.dumps({
            "settlement_status": "pending",
            "gateway_response": "timeout",
            "amount_status": "deducted_not_settled",
            "gateway_code": "GW-TIMEOUT-504",
            "processor": "stripe",
            "verification_details": {
                "bank_confirmed_debit": True,
                "merchant_received": False,
                "settlement_expected_at": "2024-01-16T10:00:00Z",
            },
        }),
        "EscalationResolutionAgent": json.dumps({
            "action": "initiate_refund",
            "priority": "high",
            "recommendation": "Immediate refund recommended. Gateway timeout caused debit without settlement.",
            "resolution_type": "auto_refund",
            "estimated_resolution_time": "24-48 hours",
            "customer_communication": "Your payment of $49.99 failed due to a gateway timeout. The amount was deducted but not received by the merchant. We are initiating an automatic refund which will be processed within 24-48 hours. Reference: REF-2024-RF-78432.",
        }),
    }
    return mocks.get(agent_name, json.dumps({"status": "processed", "message": "Analysis complete"}))


async def persist_event(
    workflow_run_id: str,
    agent_name: str,
    event_type: str,
    message: str,
    metadata: dict = None,
):
    """Persist a workflow event to the database and broadcast via WebSocket."""
    from database import async_session
    from models.workflow_event import WorkflowEvent

    event = WorkflowEvent(
        workflow_run_id=workflow_run_id,
        agent_name=agent_name,
        event_type=event_type,
        message=message,
        extra_data=metadata or {},
    )

    async with async_session() as session:
        session.add(event)
        await session.commit()

    # Broadcast to connected dashboard clients
    await ws_manager.broadcast_workflow_event(
        workflow_run_id=workflow_run_id,
        agent_name=agent_name,
        event_type=event_type,
        message=message,
        metadata=metadata,
    )


async def persist_message(
    workflow_run_id: str,
    sender: str,
    receiver: str,
    content: str,
    metadata: dict = None,
):
    """Persist an inter-agent message to the database."""
    from database import async_session
    from models.message import Message

    msg = Message(
        workflow_run_id=workflow_run_id,
        sender_agent=sender,
        receiver_agent=receiver,
        content=content,
        extra_data=metadata or {},
    )

    async with async_session() as session:
        session.add(msg)
        await session.commit()


async def _persist_token_usage(workflow_run_id: str, agent_name: str, token_info: dict):
    """Record LLM token consumption for cost tracking."""
    from database import async_session
    from models.token_usage import TokenUsage

    usage = TokenUsage(
        workflow_run_id=workflow_run_id,
        agent_name=agent_name,
        prompt_tokens=token_info.get("prompt_tokens", 0),
        completion_tokens=token_info.get("completion_tokens", 0),
        total_tokens=token_info.get("total_tokens", 0),
        model=token_info.get("model", "unknown"),
    )

    async with async_session() as session:
        session.add(usage)
        await session.commit()
