"""
Yuno AI Payment Operations Orchestrator — FastAPI Application

Main entrypoint that wires together:
- Database initialization
- API routers (agents, workflows, monitoring, WhatsApp, conversations)
- WebSocket endpoint for realtime monitoring
- CORS middleware for frontend communication
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from realtime.connection_manager import ws_manager

# Import routers
from api.agents import router as agents_router
from api.workflows import router as workflows_router
from api.monitoring import router as monitoring_router
from api.conversations import router as conversations_router
from api.whatsapp_webhook import router as whatsapp_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — initialize database tables on startup."""
    # Import all models so SQLModel registers them before create_all
    import models  # noqa: F401

    from seed import seed_database
    await seed_database()
    print(f"[START] {settings.app_name} started")
    print(f"   OpenAI: {'configured' if settings.openai_api_key else 'mock mode (no API key)'}")
    print(f"   WhatsApp: {'configured' if settings.whatsapp_token else 'simulation mode'}")
    yield
    print(f"[STOP] {settings.app_name} shutting down")


app = FastAPI(
    title=settings.app_name,
    description="Multi-agent AI orchestration platform for payment operations",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API Routers ─────────────────────────────────

app.include_router(agents_router)
app.include_router(workflows_router)
app.include_router(monitoring_router)
app.include_router(conversations_router)
app.include_router(whatsapp_router)


# ── WebSocket Endpoint ────────────────────────────────────

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """Realtime event stream for the monitoring dashboard."""
    await ws_manager.connect(websocket, room="monitoring")
    try:
        while True:
            # Keep connection alive; client sends pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, room="monitoring")


# ── Health Check ──────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "openai_configured": bool(settings.openai_api_key),
        "whatsapp_configured": bool(settings.whatsapp_token),
    }
