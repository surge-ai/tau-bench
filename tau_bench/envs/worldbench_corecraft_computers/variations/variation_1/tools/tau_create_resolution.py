import json
import uuid
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool


def _now_iso_from_data(data: Dict[str, Any]) -> str:
    """Deterministic-ish timestamp.

    If your env provides a fixed clock string in `data` (e.g. data['now'] or data['__now']),
    we use it. Otherwise we return a constant to keep eval deterministic.
    """
    for k in ("__now", "now", "current_time", "currentTime"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return "1970-01-01T00:00:00Z"


def _as_list_table(data: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    v = data.get(key)
    if v is None:
        data[key] = []
        return data[key]
    if isinstance(v, list):
        data[key] = [r for r in v if isinstance(r, dict)]
        return data[key]
    if isinstance(v, dict):
        data[key] = [r for r in v.values() if isinstance(r, dict)]
        return data[key]
    data[key] = []
    return data[key]


def _exists_by_id(data: Dict[str, Any], keys: List[str], obj_id: str) -> bool:
    for key in keys:
        table = data.get(key)
        if isinstance(table, list):
            if any(isinstance(r, dict) and r.get("id") == obj_id for r in table):
                return True
        elif isinstance(table, dict):
            if any(isinstance(r, dict) and r.get("id") == obj_id for r in table.values()):
                return True
    return False


class CreateResolution(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        ticket_id: str,
        outcome: str,
        linked_refund_id: Optional[str] = None,
        resolved_by_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Create a resolution for a support ticket."""
        # Verify ticket exists
        if not _exists_by_id(
            data,
            keys=["SupportTicket", "support_tickets", "tickets", "Ticket", "ticket"],
            obj_id=ticket_id,
        ):
            raise ValueError(f"Ticket {ticket_id} not found")

        # Verify refund exists if provided
        if linked_refund_id and not _exists_by_id(data, keys=["Refund", "refunds", "refund"], obj_id=linked_refund_id):
            raise ValueError(f"Refund {linked_refund_id} not found")

        # Verify employee exists if provided
        if resolved_by_id and not _exists_by_id(data, keys=["Employee", "employees", "employee"], obj_id=resolved_by_id):
            raise ValueError(f"Employee {resolved_by_id} not found")

        # Create row
        resolution_id = f"res_{uuid.uuid4().hex}"
        row: Dict[str, Any] = {
            "id": resolution_id,
            "type": "resolution",
            "ticketId": ticket_id,
            "outcome": outcome,
            "linkedRefundId": linked_refund_id,
            "resolvedById": resolved_by_id,
            "notes": notes,
            "createdAt": _now_iso_from_data(data),
        }

        _as_list_table(data, "Resolution").append(row)

        # Optional aliases
        if "resolutions" in data:
            _as_list_table(data, "resolutions").append(row)
        elif "resolution" in data:
            _as_list_table(data, "resolution").append(row)

        return json.dumps(row)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_resolution",
                "description": "Create a resolution record for a support ticket.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string", "description": "The support ticket ID to resolve."},
                        "outcome": {
                            "type": "string",
                            "description": "Resolution outcome. Common values: refund_approved, replacement_provided, troubleshooting_steps, order_updated, no_action.",
                        },
                        "linked_refund_id": {
                            "type": "string",
                            "description": "Optional refund ID linked to this resolution (must exist if provided).",
                        },
                        "resolved_by_id": {
                            "type": "string",
                            "description": "Optional employee ID who resolved the ticket (must exist if provided).",
                        },
                        "notes": {"type": "string", "description": "Optional resolution notes."},
                    },
                    "required": ["ticket_id", "outcome"],
                },
            },
        }
