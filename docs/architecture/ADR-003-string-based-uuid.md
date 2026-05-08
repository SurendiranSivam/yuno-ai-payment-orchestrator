# ADR-003 — String-based UUIDs for SQLite Compatibility

**Status:** Accepted  
**Date:** 2024-12-17  
**Decision Makers:** Surendiran  

---

## Context

The Yuno AI Orchestrator was initially designed with `uuid.UUID` typed primary keys in all SQLModel definitions. This works seamlessly with PostgreSQL's native `UUID` column type but fails catastrophically with SQLite.

### The Problem

SQLAlchemy maps `uuid.UUID` fields to `CHAR(32)` on SQLite and uses a type processor that calls `.hex` on the value during insertion. When UUIDs are passed as strings (common in Python code: `str(uuid.uuid4())`), the processor crashes:

```
sqlalchemy.exc.StatementError:
  (builtins.AttributeError) 'str' object has no attribute 'hex'
```

This error is silent until runtime — it passes schema creation, seed scripts, and import validation. It only surfaces when the first `Conversation` or `WorkflowRun` insert is attempted during live workflow execution.

### Why This Matters

The system must support **both** SQLite (local development, demos, CI) and PostgreSQL (production, Docker). Requiring PostgreSQL for local evaluation adds friction and blocks instant demo-ability — a critical requirement for recruiter assessments and team onboarding.

## Decision

**All UUID primary keys and foreign keys use `str` type with `uuid.uuid4().hex` as the default factory.**

### Before (broken on SQLite)
```python
class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_run_id: Optional[uuid.UUID] = Field(default=None, index=True)
```

### After (works on both SQLite and PostgreSQL)
```python
class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    workflow_run_id: Optional[str] = Field(default=None, index=True)
```

### Why `.hex` instead of `str(uuid.uuid4())`

| Format | Example | Length | Hyphens |
|---|---|---|---|
| `str(uuid.uuid4())` | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` | 36 chars | Yes |
| `uuid.uuid4().hex` | `a1b2c3d4e5f67890abcdef1234567890` | 32 chars | No |

The `.hex` format is more compact, avoids hyphen-related issues in URL parameters, and is consistent with how the seed script was already generating agent IDs.

## Models Affected

All 7 SQLModel tables were updated:

| Model | Fields Changed |
|---|---|
| `Agent` | `id` |
| `Workflow` | `id` |
| `WorkflowRun` | `id`, `workflow_id` |
| `WorkflowEvent` | `id`, `workflow_run_id` |
| `Message` | `id`, `workflow_run_id` |
| `Conversation` | `id`, `workflow_run_id` |
| `TokenUsage` | `id`, `workflow_run_id` |

## Consequences

### Pros
- Zero-config local development with SQLite — no PostgreSQL installation needed
- Identical schema works on both SQLite and PostgreSQL without conditional logic
- Compact 32-char hex strings are URL-safe and sort lexicographically
- Eliminates an entire class of runtime serialization errors

### Cons
- Loses database-level UUID type enforcement on PostgreSQL (mitigated: application-level validation via Pydantic)
- String comparison is marginally slower than native UUID comparison on PostgreSQL (negligible at expected scale)
- Requires discipline to use `.hex` consistently — a raw `str(uuid.uuid4())` would produce hyphened strings

### Alternatives Considered
- **SQLAlchemy custom type decorator:** Would handle UUID↔string conversion transparently, but adds complexity for a problem solved by a simpler type change
- **Separate model definitions per database:** Violates DRY, doubles maintenance burden
- **Force PostgreSQL everywhere:** Adds Docker dependency for local development, blocks instant evaluation
