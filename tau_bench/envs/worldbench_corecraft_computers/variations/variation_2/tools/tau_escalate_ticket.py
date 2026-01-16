import json
import hashlib
from typing import Any, Dict

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import get_now_iso_from_data
except ImportError:
    from utils import get_now_iso_from_data


class EscalateTicket(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        ticket_id: str,
        escalation_type: str,
        destination: str,
        notes: str = "",
    ) -> str:
        """Escalate an existing support ticket by creating an escalation record."""
        # Validate ticket exists
        ticket_table = data.get("support_ticket", {})
        if not isinstance(ticket_table, dict) or ticket_id not in ticket_table:
            return json.loads(json.dumps({"error": f"Ticket {ticket_id} not found"}))

        # Generate deterministic escalation ID
        id_input = f"{ticket_id}|{escalation_type}|{destination}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        escalation_id = f"esc_{id_hash}"

        # Create escalation record
        escalation = {
            "id": escalation_id,
            "type": "escalation",
            "ticketId": ticket_id,
            "escalationType": escalation_type,
            "destination": destination,
            "notes": notes,
            "createdAt": get_now_iso_from_data(data),
            "resolvedAt": None,
        }

        # Store escalation
        if "escalation" not in data or not isinstance(data["escalation"], dict):
            data["escalation"] = {}
        data["escalation"][escalation_id] = escalation

        return json.loads(json.dumps({
            "success": True,
            "escalation": escalation,
            "message": f"Ticket {ticket_id} escalated to {destination}",
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "escalate_ticket",
                "description": "Escalate an existing support ticket by creating an escalation record. Use this when a ticket needs specialized attention or higher-level review. **CRITICAL: Verify all parameters (ticket_id, escalation_type, destination, notes) are correct before calling. Escalation entities cannot be deleted once created.**",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "ID of the existing support ticket to escalate.",
                        },
                        "escalation_type": {
                            "type": "string",
                            "description": "Type of escalation: technical (for technical issues), policy_exception (for policy overrides), product_specialist (for product-specific expertise).",
                        },
                        "destination": {
                            "type": "string",
                            "description": "Escalation destination team/queue/person (e.g., 'product_specialist_team', 'technical_support_team', 'management').",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Detailed notes explaining why the escalation is needed (e.g., 'High-volume customer with 4 tickets in 30 days', 'Complex technical issue requiring specialist', 'VIP customer - platinum tier').",
                        },
                    },
                    "required": ["ticket_id", "escalation_type", "destination"],
                },
            },
        }
