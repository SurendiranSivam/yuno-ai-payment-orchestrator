"""
Customer Support Agent — first node in the payment investigation workflow.

Responsibilities:
- Receives customer complaint message
- Extracts payment issue details (amount, transaction ID, date, payment method)
- Classifies the intent (refund_request, payment_failure, fraud_report, general_inquiry)
- Passes structured analysis to downstream agents
"""

import json
from datetime import datetime

from runtime.state import PaymentWorkflowState
from runtime.agents._base import call_llm, persist_event, persist_message

SYSTEM_PROMPT = """You are a Customer Support Agent for a payment operations platform.
Your job is to analyze incoming customer complaints about payment issues.

Given a customer message, extract the following information and return as JSON:
{
    "intent": "refund_request | payment_failure | fraud_report | general_inquiry",
    "category": "payment | billing | fraud | technical",
    "extracted_details": {
        "issue_summary": "brief summary of the issue",
        "mentioned_amount": "amount if mentioned, null otherwise",
        "transaction_reference": "any reference number mentioned, null otherwise",
        "payment_method": "card/upi/bank_transfer/wallet if mentioned, null otherwise",
        "urgency": "low | medium | high"
    },
    "sentiment": "frustrated | neutral | angry | confused",
    "initial_response": "A brief empathetic acknowledgment to the customer"
}

Respond ONLY with valid JSON. No markdown, no explanation."""


async def customer_support_node(state: PaymentWorkflowState) -> dict:
    """Analyze the customer message and classify the payment issue."""
    workflow_run_id = state["workflow_run_id"]

    # Emit start event for realtime monitoring
    await persist_event(
        workflow_run_id=workflow_run_id,
        agent_name="CustomerSupportAgent",
        event_type="node_start",
        message="Analyzing customer complaint and extracting payment details...",
    )

    # Call LLM for analysis
    result, token_info = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=state["customer_message"],
        agent_name="CustomerSupportAgent",
        workflow_run_id=workflow_run_id,
    )

    # Parse LLM response
    try:
        analysis = json.loads(result)
    except json.JSONDecodeError:
        analysis = {
            "intent": "payment_failure",
            "category": "payment",
            "extracted_details": {"issue_summary": state["customer_message"], "urgency": "medium"},
            "sentiment": "frustrated",
            "initial_response": "I understand you're experiencing a payment issue. Let me investigate this for you.",
        }

    # Record inter-agent message
    await persist_message(
        workflow_run_id=workflow_run_id,
        sender="CustomerSupportAgent",
        receiver="FraudDetectionAgent",
        content=f"Issue classified: {analysis.get('intent', 'unknown')} — {analysis.get('extracted_details', {}).get('issue_summary', '')}",
    )

    await persist_event(
        workflow_run_id=workflow_run_id,
        agent_name="CustomerSupportAgent",
        event_type="node_complete",
        message=f"Classified as {analysis.get('intent', 'unknown')} with {analysis.get('extracted_details', {}).get('urgency', 'medium')} urgency",
        metadata=analysis,
    )

    return {
        "support_analysis": analysis,
        "agent_messages": state.get("agent_messages", []) + [{
            "from": "CustomerSupportAgent",
            "to": "FraudDetectionAgent",
            "content": analysis,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }
