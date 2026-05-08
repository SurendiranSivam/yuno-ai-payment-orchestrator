"""
Database Seed Script — populates the database with demo agents and workflow templates.

Run via: python seed.py
Or:      make seed
"""

import asyncio
import uuid

from database import init_db, async_session
from models.agent import Agent
from models.workflow import Workflow


# ── Demo Agents ───────────────────────────────────────────

DEMO_AGENTS = [
    {
        "name": "Customer Support Agent",
        "role": "customer_support",
        "system_prompt": "You are a Customer Support Agent specialized in payment operations. Extract issue details, classify intent, and provide empathetic initial responses.",
        "model": "gpt-4o",
        "config": {
            "tools": ["extract_payment_details", "classify_intent"],
            "channels": ["whatsapp", "api"],
            "guardrails": ["no_financial_advice", "escalate_high_value"],
            "max_retries": 2,
        },
    },
    {
        "name": "Fraud Detection Agent",
        "role": "fraud_detection",
        "system_prompt": "You are a Fraud Detection Agent. Analyze transaction patterns, calculate risk scores, and flag suspicious activities using behavioral analysis.",
        "model": "gpt-4o",
        "config": {
            "tools": ["velocity_check", "geo_analysis", "pattern_matching"],
            "risk_thresholds": {"low": 0.3, "medium": 0.6, "high": 0.8},
            "guardrails": ["require_evidence_for_flags"],
        },
    },
    {
        "name": "Payment Verification Agent",
        "role": "payment_verification",
        "system_prompt": "You are a Payment Verification Agent. Validate transaction settlement status, check gateway responses, and verify fund movements across payment processors.",
        "model": "gpt-4o",
        "config": {
            "tools": ["check_settlement", "verify_gateway", "query_processor"],
            "supported_processors": ["stripe", "razorpay", "adyen", "juspay"],
            "timeout_seconds": 30,
        },
    },
    {
        "name": "Escalation Resolution Agent",
        "role": "escalation_resolution",
        "system_prompt": "You are an Escalation Resolution Agent. Make final decisions on payment disputes based on all upstream analyses. Determine refunds, manual reviews, or auto-resolutions.",
        "model": "gpt-4o",
        "config": {
            "tools": ["initiate_refund", "create_ticket", "send_notification"],
            "auto_refund_threshold": 100.00,
            "escalation_rules": {"high_risk": "manual_review", "low_risk": "auto_resolve"},
        },
    },
]


# ── Workflow Templates ────────────────────────────────────

WORKFLOW_TEMPLATES = [
    {
        "name": "Payment Failure Investigation",
        "description": "End-to-end investigation workflow for failed payment complaints. Routes through support analysis, fraud detection, payment verification, and escalation resolution.",
        "is_template": True,
        "graph_definition": {
            "nodes": [
                {"id": "start", "type": "input", "data": {"label": "Incoming Message"}, "position": {"x": 250, "y": 0}},
                {"id": "customer_support", "type": "agent", "data": {"label": "Customer Support Agent", "role": "customer_support", "color": "#3b82f6"}, "position": {"x": 250, "y": 100}},
                {"id": "fraud_detection", "type": "agent", "data": {"label": "Fraud Detection Agent", "role": "fraud_detection", "color": "#ef4444"}, "position": {"x": 250, "y": 220}},
                {"id": "payment_verification", "type": "agent", "data": {"label": "Payment Verification Agent", "role": "payment_verification", "color": "#f59e0b"}, "position": {"x": 250, "y": 340}},
                {"id": "escalation", "type": "agent", "data": {"label": "Escalation Resolution Agent", "role": "escalation_resolution", "color": "#10b981"}, "position": {"x": 250, "y": 460}},
                {"id": "end", "type": "output", "data": {"label": "Final Response"}, "position": {"x": 250, "y": 580}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "customer_support", "animated": True},
                {"id": "e2", "source": "customer_support", "target": "fraud_detection", "label": "Issue classified"},
                {"id": "e3", "source": "fraud_detection", "target": "payment_verification", "label": "Risk assessed"},
                {"id": "e4", "source": "payment_verification", "target": "escalation", "label": "Settlement checked"},
                {"id": "e5", "source": "escalation", "target": "end", "label": "Decision made"},
            ],
        },
    },
    {
        "name": "Fraud Risk Escalation",
        "description": "Streamlined workflow for high-risk fraud alerts. Skips initial support and goes directly to fraud analysis, verification, and escalation.",
        "is_template": True,
        "graph_definition": {
            "nodes": [
                {"id": "start", "type": "input", "data": {"label": "Fraud Alert"}, "position": {"x": 250, "y": 0}},
                {"id": "fraud_detection", "type": "agent", "data": {"label": "Fraud Detection Agent", "role": "fraud_detection", "color": "#ef4444"}, "position": {"x": 250, "y": 100}},
                {"id": "payment_verification", "type": "agent", "data": {"label": "Payment Verification Agent", "role": "payment_verification", "color": "#f59e0b"}, "position": {"x": 250, "y": 220}},
                {"id": "escalation", "type": "agent", "data": {"label": "Escalation Resolution Agent", "role": "escalation_resolution", "color": "#10b981"}, "position": {"x": 250, "y": 340}},
                {"id": "end", "type": "output", "data": {"label": "Resolution"}, "position": {"x": 250, "y": 460}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "fraud_detection", "animated": True},
                {"id": "e2", "source": "fraud_detection", "target": "payment_verification", "label": "Risk scored"},
                {"id": "e3", "source": "payment_verification", "target": "escalation", "label": "Verified"},
                {"id": "e4", "source": "escalation", "target": "end", "label": "Resolved"},
            ],
        },
    },
]


async def seed_database():
    """Seed the database with demo agents and workflow templates."""
    await init_db()

    async with async_session() as session:
        # Check if already seeded
        from sqlmodel import select
        existing = (await session.execute(select(Agent).limit(1))).scalar_one_or_none()
        if existing:
            print("[SKIP] Database already seeded, skipping...")
            return

        # Seed agents
        for agent_data in DEMO_AGENTS:
            session.add(Agent(**agent_data))

        # Seed workflow templates
        for wf_data in WORKFLOW_TEMPLATES:
            session.add(Workflow(**wf_data))

        await session.commit()
        print(f"[OK] Seeded {len(DEMO_AGENTS)} agents and {len(WORKFLOW_TEMPLATES)} workflow templates")


if __name__ == "__main__":
    asyncio.run(seed_database())
