"""
WebSocket Connection Manager — broadcasts realtime workflow events to connected dashboard clients.

Supports room-based subscriptions so clients can listen to specific workflow runs
or receive all events on the global 'monitoring' room.
"""

import json
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events to subscribers."""

    def __init__(self):
        # room_name → set of active WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str = "monitoring"):
        """Accept a WebSocket connection and register it to a room."""
        await websocket.accept()
        if room not in self._connections:
            self._connections[room] = set()
        self._connections[room].add(websocket)

    def disconnect(self, websocket: WebSocket, room: str = "monitoring"):
        """Remove a WebSocket connection from its room."""
        if room in self._connections:
            self._connections[room].discard(websocket)
            if not self._connections[room]:
                del self._connections[room]

    async def broadcast(self, event: dict, room: str = "monitoring"):
        """Send a JSON event to all clients in a room. Silently drops failed sends."""
        if room not in self._connections:
            return

        payload = json.dumps(event)
        dead_connections = set()

        for ws in self._connections[room]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_connections.add(ws)

        # Clean up disconnected clients
        for ws in dead_connections:
            self._connections[room].discard(ws)

    async def broadcast_workflow_event(
        self,
        workflow_run_id: str,
        agent_name: str,
        event_type: str,
        message: str,
        metadata: dict = None,
    ):
        """Convenience method to broadcast a structured workflow event."""
        from datetime import datetime

        event = {
            "type": "workflow_event",
            "data": {
                "workflow_run_id": workflow_run_id,
                "agent_name": agent_name,
                "event_type": event_type,
                "message": message,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
        await self.broadcast(event)


# Singleton instance used across the application
ws_manager = ConnectionManager()
