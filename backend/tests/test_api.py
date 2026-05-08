"""
Tests for Agent CRUD API endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def client():
    """Create a test client."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_check(client):
    """Verify the health endpoint returns a healthy status."""
    async with client as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_agents(client):
    """Verify the agents list endpoint responds correctly."""
    async with client as ac:
        response = await ac.get("/api/agents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_whatsapp_webhook_verification(client):
    """Verify WhatsApp webhook verification handshake."""
    async with client as ac:
        response = await ac.get("/api/whatsapp/webhook", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "yuno-verify-2024",
            "hub.challenge": "12345",
        })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_whatsapp_webhook_verification_fails(client):
    """Verify webhook rejects invalid tokens."""
    async with client as ac:
        response = await ac.get("/api/whatsapp/webhook", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "12345",
        })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_stats(client):
    """Verify monitoring stats endpoint returns expected shape."""
    async with client as ac:
        response = await ac.get("/api/monitoring/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_agents" in data
    assert "total_runs" in data
    assert "total_tokens_used" in data


@pytest.mark.asyncio
async def test_list_workflows(client):
    """Verify workflows list endpoint responds correctly."""
    async with client as ac:
        response = await ac.get("/api/workflows")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_simulate_whatsapp(client):
    """Verify the WhatsApp simulation endpoint accepts messages."""
    async with client as ac:
        response = await ac.post("/api/whatsapp/simulate", json={
            "phone": "+1234567890",
            "message": "My payment failed but amount was deducted",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
