import json
import hashlib
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool


def _now_iso_from_data(data: Dict[str, Any]) -> str:
    """Get deterministic timestamp from data or use fallback."""
    for k in ("__now", "now", "current_time", "currentTime"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return "1970-01-01T00:00:00Z"


class SendNotification(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        recipient_id: str,
        recipient_type: str,
        subject: str,
        message: str,
        channel: str = "email",
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
    ) -> str:
        """Send notification to a customer or employee via email, SMS, or in-app."""
        # Validate recipient exists
        recipient_map = {
            "customer": "customer",
            "employee": "employee",
        }

        recipient_table_key = recipient_map.get(recipient_type.lower())
        if not recipient_table_key:
            return json.loads(json.dumps({"error": f"Unknown recipient type: {recipient_type}"}))

        recipient_table = data.get(recipient_table_key, {})
        if not isinstance(recipient_table, dict) or recipient_id not in recipient_table:
            return json.loads(json.dumps({"error": f"{recipient_type.capitalize()} {recipient_id} not found"}))

        recipient = recipient_table[recipient_id]

        # Validate channel
        valid_channels = ["email", "sms", "in_app", "push"]
        if channel.lower() not in valid_channels:
            return json.loads(json.dumps({"error": f"Invalid channel: {channel}. Valid: {', '.join(valid_channels)}"}))

        # Generate notification ID
        id_input = f"{recipient_id}|{subject}|{_now_iso_from_data(data)}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        notification_id = f"notif_{id_hash}"

        # Create notification record
        notification = {
            "id": notification_id,
            "type": "notification",
            "recipientId": recipient_id,
            "recipientType": recipient_type,
            "recipientEmail": recipient.get("email"),
            "recipientPhone": recipient.get("phone"),
            "subject": subject,
            "message": message,
            "channel": channel.lower(),
            "status": "sent",
            "relatedEntityType": related_entity_type,
            "relatedEntityId": related_entity_id,
            "sentAt": _now_iso_from_data(data),
        }

        # Store notification (in practice this would trigger actual sending)
        if "notification" not in data or not isinstance(data["notification"], dict):
            data["notification"] = {}
        data["notification"][notification_id] = notification

        return json.loads(json.dumps({
            "success": True,
            "notification": notification,
            "message": f"Notification {notification_id} sent via {channel} to {recipient.get('email') or recipient.get('phone')}",
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "send_notification",
                "description": "Send notification to a customer or employee via email, SMS, push, or in-app channels.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient_id": {
                            "type": "string",
                            "description": "ID of the recipient (customer or employee).",
                        },
                        "recipient_type": {
                            "type": "string",
                            "description": "Type of recipient: customer or employee.",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Notification subject/title.",
                        },
                        "message": {
                            "type": "string",
                            "description": "Notification message body.",
                        },
                        "channel": {
                            "type": "string",
                            "description": "Communication channel: email, sms, in_app, or push (default: email).",
                        },
                        "related_entity_type": {
                            "type": "string",
                            "description": "Optional type of related entity (order, ticket, payment, etc.).",
                        },
                        "related_entity_id": {
                            "type": "string",
                            "description": "Optional ID of related entity.",
                        },
                    },
                    "required": ["recipient_id", "recipient_type", "subject", "message"],
                },
            },
        }
