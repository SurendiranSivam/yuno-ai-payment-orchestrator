"""
Payment Verification Agent — validates transaction status and settlement.

Responsibilities:
- Checks transaction settlement status
- Verifies payment gateway response
- Confirms whether amount was successfully settled
- Passes verification result to Escalation Agent
"""

import json
from datetime import datetime

from runtime.state import PaymentWorkflowState
from runtime.agents._base import call_llm, persist_event, persist_message

SYSTEM_PROMPT = """You are a Payment Verification Agent for a payment operations platform.
You verify the actual status of payment transactions with payment processors.

Given fraud assessment and support analysis, verify the payment status and return as JSON:
{
    "settlement_status": "settled | pending | failed | reversed",
    "gateway_response": "success | timeout | declined | error",
    "amount_status": "deducted_and_settled | deducted_not_settled | not_deducted | reversed",
    "gateway_code": "gateway-specific response code",
    "processor": "stripe | razorpay | adyen | juspay",
    "verification_details": {
        "bank_confirmed_debit": true/false,
        "merchant_received": true/false,
        "settlement_expected_at": "ISO timestamp or null"
    }
}

Simulate realistic payment gateway verification results.
Respond ONLY with valid JSON."""


async def payment_verification_node(state: PaymentWorkflowState) -> dict:
    """Verify transaction settlement status with payment processor."""
    workflow_run_id = state["workflow_run_id"]

    await persist_event(
        workflow_run_id=workflow_run_id,
        agent_name="PaymentVerificationAgent",
        event_type="node_start",
        message="Verifying transaction settlement with payment gateway...",
    )

    context = (
        f"Support Analysis: {json.dumps(state.get('support_analysis', {}))}\n"
        f"Fraud Assessment: {json.dumps(state.get('fraud_assessment', {}))}\n"
        f"Original Message: {state['customer_message']}"
    )

    result, token_info = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=context,
        agent_name="PaymentVerificationAgent",
        workflow_run_id=workflow_run_id,
    )

    try:
        verification = json.loads(result)
    except json.JSONDecodeError:
        verification = {"settlement_status": "pending", "gateway_response": "timeout", "amount_status": "deducted_not_settled"}

    await persist_message(
        workflow_run_id=workflow_run_id,
        sender="PaymentVerificationAgent",
        receiver="EscalationResolutionAgent",
        content=f"Settlement: {verification.get('settlement_status', 'unknown')} — Amount: {verification.get('amount_status', 'unknown')}",
    )

    await persist_event(
        workflow_run_id=workflow_run_id,
        agent_name="PaymentVerificationAgent",
        event_type="node_complete",
        message=f"Settlement {verification.get('settlement_status', 'unknown')} — Gateway: {verification.get('gateway_response', 'unknown')}",
        metadata=verification,
    )

    return {
        "verification_result": verification,
        "agent_messages": state.get("agent_messages", []) + [{
            "from": "PaymentVerificationAgent",
            "to": "EscalationResolutionAgent",
            "content": verification,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }
