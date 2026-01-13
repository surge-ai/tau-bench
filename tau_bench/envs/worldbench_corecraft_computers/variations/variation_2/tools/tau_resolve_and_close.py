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


class ResolveAndClose(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        ticket_id: str,
        resolution_type: str,
        resolution_notes: str,
        notify_customer: bool = True,
    ) -> str:
        """Workflow tool: Create resolution, close ticket, and optionally send notification - all in one step."""
        # Validate ticket
        ticket_table = data.get("support_ticket", {})
        if not isinstance(ticket_table, dict) or ticket_id not in ticket_table:
            return json.loads(json.dumps({"error": f"Ticket {ticket_id} not found"}))

        ticket = ticket_table[ticket_id]
        customer_id = ticket.get("customerId")

        # Create resolution
        res_id_input = f"{ticket_id}|{resolution_type}|{_now_iso_from_data(data)}"
        res_id_hash = hashlib.sha256(res_id_input.encode()).hexdigest()[:12]
        resolution_id = f"res_{res_id_hash}"

        resolution = {
            "id": resolution_id,
            "type": "resolution",
            "ticketId": ticket_id,
            "resolutionType": resolution_type,
            "description": resolution_notes,
            "createdAt": _now_iso_from_data(data),
        }

        # Store resolution
        if "resolution" not in data or not isinstance(data["resolution"], dict):
            data["resolution"] = {}
        data["resolution"][resolution_id] = resolution

        # Update and close ticket
        ticket["status"] = "resolved"
        ticket["resolvedAt"] = _now_iso_from_data(data)
        ticket["updatedAt"] = _now_iso_from_data(data)

        # Send notification if requested
        notification = None
        if notify_customer and customer_id:
            customer_table = data.get("customer", {})
            if isinstance(customer_table, dict) and customer_id in customer_table:
                customer = customer_table[customer_id]

                notif_id_input = f"{customer_id}|ticket_resolved|{_now_iso_from_data(data)}"
                notif_id_hash = hashlib.sha256(notif_id_input.encode()).hexdigest()[:12]
                notification_id = f"notif_{notif_id_hash}"

                notification = {
                    "id": notification_id,
                    "type": "notification",
                    "recipientId": customer_id,
                    "recipientType": "customer",
                    "recipientEmail": customer.get("email"),
                    "subject": f"Your ticket {ticket_id} has been resolved",
                    "message": f"Your issue has been resolved: {resolution_notes}",
                    "channel": "email",
                    "status": "sent",
                    "relatedEntityType": "ticket",
                    "relatedEntityId": ticket_id,
                    "sentAt": _now_iso_from_data(data),
                }

                if "notification" not in data or not isinstance(data["notification"], dict):
                    data["notification"] = {}
                data["notification"][notification_id] = notification

        return json.loads(json.dumps({
            "success": True,
            "resolution": resolution,
            "updated_ticket": ticket,
            "notification": notification,
            "customer_notified": notification is not None,
            "message": f"Ticket {ticket_id} resolved and closed" +
                      (" with customer notification sent" if notification else ""),
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "resolve_and_close",
                "description": "Workflow tool: Create resolution, close ticket, and optionally notify customer - all in one atomic operation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "Ticket ID to resolve and close.",
                        },
                        "resolution_type": {
                            "type": "string",
                            "description": "Type of resolution: refund_issued, replacement_sent, technical_fix, policy_override, no_action_needed.",
                        },
                        "resolution_notes": {
                            "type": "string",
                            "description": "Detailed notes about how the issue was resolved.",
                        },
                        "notify_customer": {
                            "type": "boolean",
                            "description": "Whether to send notification to customer (default: true).",
                        },
                    },
                    "required": ["ticket_id", "resolution_type", "resolution_notes"],
                },
            },
        }
