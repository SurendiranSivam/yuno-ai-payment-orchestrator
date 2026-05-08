"""
Workflow Orchestrator — builds and executes LangGraph workflows for payment operations.

This is the core engine that:
1. Constructs a StateGraph with agent nodes
2. Defines the execution flow (support → fraud → verification → escalation)
3. Manages workflow lifecycle (create run → execute → persist results)
4. Handles async execution and error recovery
"""

import uuid
from datetime import datetime

from langgraph.graph import StateGraph, START, END

from runtime.state import PaymentWorkflowState
from runtime.agents.customer_support import customer_support_node
from runtime.agents.fraud_detection import fraud_detection_node
from runtime.agents.payment_verification import payment_verification_node
from runtime.agents.escalation_resolution import escalation_resolution_node
from runtime.agents._base import persist_event
from realtime.connection_manager import ws_manager


class WorkflowOrchestrator:
    """Builds and executes LangGraph payment investigation workflows."""

    def __init__(self):
        self._graph = self._build_graph()

    def _build_graph(self):
        """Construct the payment investigation StateGraph."""
        builder = StateGraph(PaymentWorkflowState)

        # Register agent nodes
        builder.add_node("customer_support", customer_support_node)
        builder.add_node("fraud_detection", fraud_detection_node)
        builder.add_node("payment_verification", payment_verification_node)
        builder.add_node("escalation_resolution", escalation_resolution_node)

        # Define linear execution flow
        builder.add_edge(START, "customer_support")
        builder.add_edge("customer_support", "fraud_detection")
        builder.add_edge("fraud_detection", "payment_verification")
        builder.add_edge("payment_verification", "escalation_resolution")
        builder.add_edge("escalation_resolution", END)

        return builder.compile()

    async def execute_workflow(
        self,
        customer_message: str,
        customer_phone: str = "unknown",
        workflow_id: str = None,
        trigger_source: str = "manual",
    ) -> dict:
        """
        Execute the full payment investigation workflow.

        Creates a workflow run record, executes the LangGraph pipeline,
        persists results, and returns the complete execution output.
        """
        from database import async_session
        from models.workflow_run import WorkflowRun
        from models.conversation import Conversation

        workflow_run_id = str(uuid.uuid4())

        # Default to the payment failure investigation template
        if not workflow_id:
            workflow_id = await self._get_default_workflow_id()

        # Create workflow run record
        run = WorkflowRun(
            id=workflow_run_id,
            workflow_id=workflow_id,
            status="running",
            trigger_source=trigger_source,
            input_data={
                "customer_message": customer_message,
                "customer_phone": customer_phone,
            },
        )

        async with async_session() as session:
            session.add(run)
            # Persist inbound conversation if from WhatsApp
            if trigger_source == "whatsapp":
                session.add(Conversation(
                    workflow_run_id=workflow_run_id,
                    user_phone=customer_phone,
                    direction="inbound",
                    message=customer_message,
                ))
            await session.commit()

        # Broadcast workflow start
        await ws_manager.broadcast({
            "type": "workflow_started",
            "data": {
                "workflow_run_id": workflow_run_id,
                "trigger_source": trigger_source,
                "customer_phone": customer_phone,
                "timestamp": datetime.utcnow().isoformat(),
            },
        })

        # Build initial state
        initial_state: PaymentWorkflowState = {
            "customer_message": customer_message,
            "customer_phone": customer_phone,
            "workflow_run_id": workflow_run_id,
            "support_analysis": {},
            "fraud_assessment": {},
            "verification_result": {},
            "escalation_decision": {},
            "agent_messages": [],
            "final_response": "",
            "status": "running",
            "error": None,
        }

        # Execute the LangGraph workflow
        try:
            result = await self._graph.ainvoke(initial_state)

            # Update workflow run with results
            async with async_session() as session:
                from sqlmodel import select
                stmt = select(WorkflowRun).where(WorkflowRun.id == workflow_run_id)
                db_run = (await session.execute(stmt)).scalar_one()
                db_run.status = "completed"
                db_run.completed_at = datetime.utcnow()
                db_run.output_data = {
                    "support_analysis": result.get("support_analysis", {}),
                    "fraud_assessment": result.get("fraud_assessment", {}),
                    "verification_result": result.get("verification_result", {}),
                    "escalation_decision": result.get("escalation_decision", {}),
                    "final_response": result.get("final_response", ""),
                }
                session.add(db_run)
                await session.commit()

            # Broadcast completion
            await ws_manager.broadcast({
                "type": "workflow_completed",
                "data": {
                    "workflow_run_id": workflow_run_id,
                    "status": "completed",
                    "final_response": result.get("final_response", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            })

            return {
                "workflow_run_id": workflow_run_id,
                "status": "completed",
                "final_response": result.get("final_response", ""),
                "output": result,
            }

        except Exception as e:
            # Mark workflow as failed
            async with async_session() as session:
                from sqlmodel import select
                stmt = select(WorkflowRun).where(WorkflowRun.id == workflow_run_id)
                db_run = (await session.execute(stmt)).scalar_one()
                db_run.status = "failed"
                db_run.completed_at = datetime.utcnow()
                db_run.output_data = {"error": str(e)}
                session.add(db_run)
                await session.commit()

            await persist_event(
                workflow_run_id=workflow_run_id,
                agent_name="Orchestrator",
                event_type="error",
                message=f"Workflow execution failed: {str(e)[:200]}",
            )

            return {
                "workflow_run_id": workflow_run_id,
                "status": "failed",
                "error": str(e),
            }

    async def _get_default_workflow_id(self) -> str:
        """Get the default payment failure investigation workflow ID."""
        from database import async_session
        from models.workflow import Workflow
        from sqlmodel import select

        async with async_session() as session:
            stmt = select(Workflow).where(Workflow.is_template == True).limit(1)
            workflow = (await session.execute(stmt)).scalar_one_or_none()
            if workflow:
                return str(workflow.id)
            # Return a placeholder UUID if no templates exist yet
            return str(uuid.uuid4())


# Singleton orchestrator instance
orchestrator = WorkflowOrchestrator()
