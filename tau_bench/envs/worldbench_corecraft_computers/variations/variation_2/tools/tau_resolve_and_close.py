import json
import hashlib
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import get_now_iso_from_data
except ImportError:
    from utils import get_now_iso_from_data


class ResolveAndClose(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        ticket_id: str,
        resolution_type: str,
    ) -> str:
        """Workflow tool: Create resolution and close ticket in one atomic operation."""
        # Validate ticket
        ticket_table = data.get("support_ticket", {})
        if not isinstance(ticket_table, dict) or ticket_id not in ticket_table:
            return json.loads(json.dumps({"error": f"Ticket {ticket_id} not found"}))

        ticket = ticket_table[ticket_id]

        # Create resolution
        res_id_input = f"{ticket_id}|{resolution_type}|{get_now_iso_from_data(data)}"
        res_id_hash = hashlib.sha256(res_id_input.encode()).hexdigest()[:12]
        resolution_id = f"res_{res_id_hash}"

        resolution = {
            "id": resolution_id,
            "type": "resolution",
            "ticketId": ticket_id,
            "outcome": resolution_type,
            "createdAt": get_now_iso_from_data(data),
        }

        # Store resolution
        if "resolution" not in data or not isinstance(data["resolution"], dict):
            data["resolution"] = {}
        data["resolution"][resolution_id] = resolution

        # Update and close ticket
        ticket["status"] = "resolved"
        ticket["updatedAt"] = get_now_iso_from_data(data)

        return json.loads(json.dumps({
            "success": True,
            "resolution": resolution,
            "updated_ticket": ticket,
            "message": f"Ticket {ticket_id} resolved and closed",
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "resolve_and_close",
                "description": "Workflow tool: Create resolution and close ticket in one atomic operation. **CRITICAL: Verify all parameters (ticket_id, resolution_type) are correct before calling. Resolution entities cannot be deleted once created.**",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "Ticket ID to resolve and close.",
                        },
                        "resolution_type": {
                            "type": "string",
                            "description": "Type of resolution (maps to outcome field): refund_issued, replacement_sent, recommendation_provided, troubleshooting_steps, order_updated, no_action.",
                        },
                    },
                    "required": ["ticket_id", "resolution_type"],
                },
            },
        }
