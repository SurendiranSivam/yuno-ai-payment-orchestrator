# ADR-002 — WebSocket-First Real-time Monitoring

**Status:** Accepted  
**Date:** 2024-12-16  
**Decision Makers:** Surendiran  

---

## Context

The operations dashboard needs to display workflow execution progress in real-time. As each agent starts and completes processing, the dashboard must update immediately — not on the next page refresh or polling interval.

We evaluated three approaches:

| Approach | Latency | Complexity | Scalability |
|---|---|---|---|
| **HTTP Polling** (2-5s interval) | 1-5s | Low | High (stateless) |
| **Server-Sent Events** (SSE) | ~100ms | Medium | Medium (one-way) |
| **WebSocket** (bidirectional) | ~50ms | Medium | Medium (stateful) |

## Decision

**WebSocket connections** with a room-based `ConnectionManager` for real-time event broadcasting.

### Rationale

1. **Sub-second latency is essential for live demos.** When showing the orchestrator to stakeholders, a 2-5 second polling delay makes the system feel laggy. WebSocket delivers events in ~50ms, creating the impression of an instantly responsive system.

2. **Bidirectional communication future-proofs the architecture.** While the current implementation is server→client broadcast, WebSockets enable future client→server interactions like pausing workflows, injecting human approvals, or subscribing to specific workflow runs.

3. **Event-driven architecture aligns with the agent execution model.** Agents already call `persist_event()` after each action. Adding `ws_manager.broadcast()` to the same function means zero additional orchestration logic — the monitoring layer piggybacks on existing event persistence.

4. **Room-based subscriptions prevent unnecessary traffic.** Dashboard clients join the `monitoring` room. Future per-workflow detail views can join `workflow:{run_id}` rooms for targeted event streams.

## Implementation Details

```
Agent node executes
    ↓
persist_event()
    ├── DB write (WorkflowEvent table)
    └── ws_manager.broadcast_workflow_event()
            ↓
        All clients in "monitoring" room receive JSON:
        {
            "type": "workflow_event",
            "data": {
                "agent_name": "FraudDetectionAgent",
                "event_type": "node_complete",
                "message": "Risk Score: 0.15 — LOW"
            }
        }
```

### Client-side Resilience
- Exponential backoff reconnection: 1s → 2s → 4s → ... → 30s max
- `useRef` for event callback to prevent React re-render reconnection loops
- SSR guard to prevent WebSocket instantiation during server-side rendering

## Consequences

### Pros
- Real-time dashboard updates create a compelling demo experience
- Event broadcasting is co-located with event persistence — single function call
- Room-based architecture supports multi-tenant monitoring in the future
- Client reconnection is automatic and transparent to the user

### Cons
- WebSocket connections are stateful — harder to load-balance than stateless HTTP
- In-memory `ConnectionManager` doesn't scale across multiple server processes (production fix: Redis pub/sub adapter)
- Dead connections require periodic cleanup (implemented via ping/pong keepalive)

### Alternatives Rejected
- **HTTP Polling:** Unacceptable latency for live monitoring demos
- **SSE:** One-directional only; forecloses future interactive features (human-in-the-loop approvals, workflow pausing)
- **gRPC Streaming:** Overkill for browser clients; would require a proxy layer
