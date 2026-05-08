"""
Fraud Detection Agent — analyzes transaction patterns and calculates risk.

Responsibilities:
- Receives support analysis from upstream
- Analyzes transaction for fraud indicators
- Calculates risk score (0.0 – 1.0)
- Flags suspicious patterns
- Passes assessment to Payment Verification Agent
"""

import json
from datetime import datetime

from runtime.state import PaymentWorkflowState
from runtime.agents._base import call_llm, persist_event, persist_message

SYSTEM_PROMPT = """You are a Fraud Detection Agent for a payment operations platform.
You analyze payment transactions for fraud indicators.

Given a customer support analysis of a payment issue, perform fraud assessment and return as JSON:
{
    "risk_score": 0.0 to 1.0,
    "risk_level": "low | medium | high | critical",
    "flags": ["list of any fraud indicators found"],
    "analysis": "brief explanation of the risk assessment",
    "recommendation": "proceed_with_verification | hold_for_review | block_transaction",
    "checked_patterns": ["velocity_check", "geo_anomaly", "amount_deviation", "device_fingerprint"]
}

Consider: transaction velocity, geographic anomalies, amount deviations, repeat patterns.
Respond ONLY with valid JSON."""


async def fraud_detection_node(state: PaymentWorkflowState) -> dict:
    """Analyze the transaction for fraud indicators and calculate risk."""
    workflow_run_id = state["workflow_run_id"]
    support_analysis = state.get("support_analysis", {})

    await persist_event(
        workflow_run_id=workflow_run_id,
        agent_name="FraudDetectionAgent",
        event_type="node_start",
        message="Running fraud pattern analysis and risk scoring...",
    )

    context = f"Support Analysis: {json.dumps(support_analysis)}\nOriginal Message: {state['customer_message']}"

    result, token_info = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=context,
        agent_name="FraudDetectionAgent",
        workflow_run_id=workflow_run_id,
    )

    try:
        assessment = json.loads(result)
    except json.JSONDecodeError:
        assessment = {"risk_score": 0.1, "risk_level": "low", "flags": [], "analysis": "Unable to parse", "recommendation": "proceed_with_verification"}

    await persist_message(
        workflow_run_id=workflow_run_id,
        sender="FraudDetectionAgent",
        receiver="PaymentVerificationAgent",
        content=f"Risk Level: {assessment.get('risk_level', 'unknown')} (Score: {assessment.get('risk_score', 0)})",
    )

    await persist_event(
        workflow_run_id=workflow_run_id,
        agent_name="FraudDetectionAgent",
        event_type="node_complete",
        message=f"Risk Score: {assessment.get('risk_score', 0)} — {assessment.get('risk_level', 'unknown').upper()}",
        metadata=assessment,
    )

    return {
        "fraud_assessment": assessment,
        "agent_messages": state.get("agent_messages", []) + [{
            "from": "FraudDetectionAgent",
            "to": "PaymentVerificationAgent",
            "content": assessment,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }
