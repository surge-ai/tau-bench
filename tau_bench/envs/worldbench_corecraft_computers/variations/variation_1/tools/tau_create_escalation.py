# typed: ignore
# Tau Bench write tool: create_escalation
#
# Converted from create_escalation.py (legacy SQL tool) to Tau's Tool interface.
# This implementation mutates the canonical `data` dict in-place (Tau-style).
#
# Original behavior (SQL):
# - Verify SupportTicket exists
# - INSERT into Escalation(id, type, ticketId, escalationType, destination, notes, createdAt, resolvedAt)
# - createdAt = datetime('now') ; resolvedAt = NULL
# - Return the created escalation row

import json
import uuid
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


def _as_list_table(data: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    """Ensure `data[key]` is a list-of-dicts table, returning it."""
    v = data.get(key)
    if v is None:
        data[key] = []
        return data[key]
    if isinstance(v, list):
        # best effort: keep only dict rows
        data[key] = [r for r in v if isinstance(r, dict)]
        return data[key]
    if isinstance(v, dict):
        data[key] = [r for r in v.values() if isinstance(r, dict)]
        return data[key]
    data[key] = []
    return data[key]


def _find_ticket(data: Dict[str, Any], ticket_id: str) -> Optional[Dict[str, Any]]:
    for key in ("SupportTicket", "support_ticket", "supportticket", "support_tickets", "supportTickets"):
        table = data.get(key)
        if isinstance(table, list):
            for r in table:
                if isinstance(r, dict) and r.get("id") == ticket_id:
                    return r
        elif isinstance(table, dict):
            for r in table.values():
                if isinstance(r, dict) and r.get("id") == ticket_id:
                    return r
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

        escalation_id = f"esc_{uuid.uuid4().hex}"
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

        # Prefer the canonical "Escalation" table name from your legacy SQL.
        table = _as_list_table(data, "Escalation")
        table.append(row)

        # Optional: keep a lowercase alias if your other tools query `escalation`/`escalations`
        if "escalations" in data:
            _as_list_table(data, "escalations").append(row)
        elif "escalation" in data:
            _as_list_table(data, "escalation").append(row)

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
