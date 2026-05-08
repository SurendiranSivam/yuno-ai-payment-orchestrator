# ADR-001 — LangGraph for Multi-Agent Orchestration

**Status:** Accepted  
**Date:** 2024-12-15  
**Decision Makers:** Surendiran  

---

## Context

The Yuno AI Orchestrator requires a framework to coordinate multiple AI agents in a payment dispute investigation pipeline. Each agent performs a distinct function (support analysis, fraud detection, payment verification, escalation resolution) and must execute in a specific order with shared state.

We evaluated three approaches:

| Framework | Model | Control Flow |
|---|---|---|
| **AutoGen** | Autonomous multi-agent conversations | Implicit — agents decide when to hand off |
| **CrewAI** | Task-based crew delegation | Semi-structured — crew roles guide flow |
| **LangGraph** | Directed graph with typed state | Explicit — `StateGraph` defines exact edges |

## Decision

**LangGraph `StateGraph`** was selected as the orchestration engine.

### Rationale

1. **Deterministic execution is non-negotiable for financial operations.** A payment fraud assessment must always happen before an escalation decision. Autonomous agent frameworks cannot guarantee this — an agent might skip fraud detection entirely if the conversation drifts.

2. **Typed shared state prevents data loss between agents.** The `PaymentWorkflowState` TypedDict ensures every agent writes to an explicit field (`support_analysis`, `fraud_assessment`, etc.) rather than relying on unstructured message passing.

3. **Graph-level error recovery.** When an agent fails mid-execution, LangGraph surfaces the error at the graph level. The orchestrator catches it, marks the run as `failed`, persists the partial state, and broadcasts the error — all without losing upstream agent work.

4. **Observability is built into the execution model.** Every state transition corresponds to a graph edge, making it trivial to persist `node_start` / `node_complete` events for real-time monitoring.

## Consequences

### Pros
- Guaranteed execution order prevents investigation gaps
- TypedDict state ensures structured data flow between agents
- Graph compilation catches wiring errors at startup, not runtime
- Natural fit for React Flow visualization — graph nodes map 1:1 to UI nodes

### Cons
- Less flexible than conversational agent frameworks for open-ended tasks
- Sequential execution means agents can't run in parallel (mitigated: LangGraph supports parallel branches for future optimization)
- Steeper learning curve compared to simple chain-of-calls patterns

### Alternatives Rejected
- **Raw asyncio chains:** No state management, no error recovery at pipeline level
- **Celery task chains:** Heavyweight for in-process orchestration, designed for distributed workers
- **AutoGen:** Excellent for research/exploration, but non-deterministic control flow is unacceptable for financial operations
