"""
WhatsApp Cloud API Client — sends and receives messages via Meta's WhatsApp Business API.

Handles:
- Sending text replies to users
- Parsing incoming webhook payloads
- Webhook verification handshake
"""

import httpx
from config import get_settings

WHATSAPP_API_BASE = "https://graph.facebook.com/v21.0"


class WhatsAppClient:
    """Lightweight async client for WhatsApp Cloud API."""

    def __init__(self):
        settings = get_settings()
        self.token = settings.whatsapp_token
        self.phone_number_id = settings.whatsapp_phone_number_id

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def send_text_message(self, to: str, body: str) -> dict:
        """Send a text message to a WhatsApp user."""
        url = f"{WHATSAPP_API_BASE}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self._headers)
            return response.json()

    @staticmethod
    def extract_message_from_payload(payload: dict) -> dict | None:
        """
        Parse an incoming WhatsApp webhook payload and extract the message.
        Returns dict with 'phone', 'message', 'message_id' or None if not a message event.
        """
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            if not messages:
                return None

            msg = messages[0]
            contact = value.get("contacts", [{}])[0]

            return {
                "phone": msg.get("from", ""),
                "message": msg.get("text", {}).get("body", ""),
                "message_id": msg.get("id", ""),
                "contact_name": contact.get("profile", {}).get("name", "Unknown"),
            }
        except (IndexError, KeyError):
            return None


# Singleton client instance
whatsapp_client = WhatsAppClient()
