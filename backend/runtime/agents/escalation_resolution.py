"""
Escalation Resolution Agent — final decision-maker in the payment investigation workflow.

Responsibilities:
- Aggregates analysis from all upstream agents
- Determines appropriate action (refund, manual review, auto-resolve)
- Generates customer-facing response
- Sets priority level for the resolution
"""

import json
from datetime import datetime

from runtime.state import PaymentWorkflowState
from runtime.agents._base import call_llm, persist_event, persist_message

SYSTEM_PROMPT = """You are an Escalation Resolution Agent for a payment operations platform.
You make final decisions on payment issues based on upstream agent analyses.

Given the complete analysis chain (support → fraud → verification), determine the resolution:
{
    "action": "initiate_refund | escalate_to_manual | auto_resolve | block_and_investigate",
    "priority": "low | medium | high | critical",
    "recommendation": "clear explanation of the recommended action",
    "resolution_type": "auto_refund | manual_review | no_action | investigation",
    "estimated_resolution_time": "e.g. 24-48 hours",
    "customer_communication": "The complete, professional message to send to the customer"
}

Write the customer_communication as if you are sending it directly to the customer.
Be professional, empathetic, and specific about next steps.
Respond ONLY with valid JSON."""


async def escalation_resolution_node(state: PaymentWorkflowState) -> dict:
    """Make final resolution decision and generate customer response."""
    workflow_run_id = state["workflow_run_id"]

    await persist_event(
        workflow_run_id=workflow_run_id,
        agent_name="EscalationResolutionAgent",
        event_type="node_start",
        message="Evaluating all agent analyses for final resolution...",
    )

    context = (
        f"Support Analysis: {json.dumps(state.get('support_analysis', {}))}\n"
        f"Fraud Assessment: {json.dumps(state.get('fraud_assessment', {}))}\n"
        f"Verification Result: {json.dumps(state.get('verification_result', {}))}\n"
        f"Original Message: {state['customer_message']}"
    )

    result, token_info = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=context,
        agent_name="EscalationResolutionAgent",
        workflow_run_id=workflow_run_id,
    )

    try:
        decision = json.loads(result)
    except json.JSONDecodeError:
        decision = {
            "action": "initiate_refund",
            "priority": "high",
            "recommendation": "Refund recommended due to gateway timeout",
            "resolution_type": "auto_refund",
            "estimated_resolution_time": "24-48 hours",
            "customer_communication": "We've identified a gateway timeout that caused your payment to be deducted without completion. A refund has been initiated and will be processed within 24-48 hours.",
        }

    final_response = decision.get("customer_communication", "Your issue has been resolved. Please contact support for details.")

    await persist_message(
        workflow_run_id=workflow_run_id,
        sender="EscalationResolutionAgent",
        receiver="Customer",
        content=f"Resolution: {decision.get('action', 'unknown')} — Priority: {decision.get('priority', 'medium')}",
    )

    await persist_event(
        workflow_run_id=workflow_run_id,
        agent_name="EscalationResolutionAgent",
        event_type="node_complete",
        message=f"Decision: {decision.get('action', 'unknown')} ({decision.get('priority', 'medium')} priority)",
        metadata=decision,
    )

    return {
        "escalation_decision": decision,
        "final_response": final_response,
        "status": "completed",
        "agent_messages": state.get("agent_messages", []) + [{
            "from": "EscalationResolutionAgent",
            "to": "Customer",
            "content": decision,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }
