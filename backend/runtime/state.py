"""
Workflow State — TypedDict defining the shared state passed between LangGraph agent nodes.

Each agent reads from and writes to this state during workflow execution.
The state accumulates analysis results as the workflow progresses through
the agent pipeline.
"""

from typing import TypedDict, List, Optional


class PaymentWorkflowState(TypedDict):
    """Shared state for the payment investigation workflow."""

    # ── Input ─────────────────────────────────────────────
    customer_message: str
    customer_phone: str
    workflow_run_id: str

    # ── Agent Outputs (accumulated as workflow progresses) ─
    support_analysis: dict       # Intent classification, extracted details
    fraud_assessment: dict       # Risk score, risk level, flags
    verification_result: dict    # Settlement status, gateway response
    escalation_decision: dict    # Action, priority, recommendation

    # ── Orchestration Metadata ────────────────────────────
    agent_messages: List[dict]   # Inter-agent message log
    final_response: str          # Response to send back to customer
    status: str                  # running / completed / failed
    error: Optional[str]        # Error message if workflow fails
