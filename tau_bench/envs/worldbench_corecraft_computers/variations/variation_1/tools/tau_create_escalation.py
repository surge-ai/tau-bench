import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from tau_bench.envs.tool import Tool


def _now_iso_from_data(data: Dict[str, Any]) -> str:
    """Deterministic-ish timestamp.

    If your env provides a fixed clock in `data` (e.g. data['now'] or data['__now']),
    we use it. Otherwise we fall back to a constant to avoid non-determinism in eval.
    """
    for k in ("__now", "now", "current_time", "currentTime"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # fallback: constant (prefer deterministic over wall clock)
    return "1970-01-01T00:00:00Z"




def _find_ticket(data: Dict[str, Any], ticket_id: str) -> Optional[Dict[str, Any]]:
    ticket_table = data.get("support_ticket")
    if isinstance(ticket_table, dict) and ticket_id in ticket_table:
        return ticket_table[ticket_id]
    return None


class CreateEscalation(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        ticket_id: str,
        escalation_type: str,
        destination: str,
        notes: Optional[str] = None,
    ) -> str:
        """Create an escalation record linked to an existing support ticket."""
        if not _find_ticket(data, ticket_id):
            raise ValueError(f"Ticket {ticket_id} not found")

        # Generate deterministic ID based on input parameters
        id_input = f"{ticket_id}|{escalation_type}|{destination}|{notes or ''}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        escalation_id = f"esc_{id_hash}"
        row: Dict[str, Any] = {
            "id": escalation_id,
            "type": "escalation",
            "ticketId": ticket_id,
            "escalationType": escalation_type,
            "destination": destination,
            "notes": notes,
            "createdAt": _now_iso_from_data(data),
            "resolvedAt": None,
        }

        # Use dictionary format keyed by ID
        if "escalation" not in data or not isinstance(data["escalation"], dict):
            data["escalation"] = {}
        data["escalation"][escalation_id] = row

        return json.dumps(row)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_escalation",
                "description": "Create an escalation record for a support ticket.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string", "description": "Support ticket id to escalate."},
                        "escalation_type": {"type": "string", "description": "Escalation type (free-form or constrained by rules)."},
                        "destination": {"type": "string", "description": "Escalation destination (team/queue/person)."},
                        "notes": {"type": "string", "description": "Optional notes for the escalation."},
                    },
                    "required": ["ticket_id", "escalation_type", "destination"],
                },
            },
        }
