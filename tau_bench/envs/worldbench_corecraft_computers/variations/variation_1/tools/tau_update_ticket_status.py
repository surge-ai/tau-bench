import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

from .data_utils import validate_enum


# Valid closure reasons for tickets
VALID_CLOSURE_REASONS = [
    "resolved_success",
    "customer_abandoned",
    "duplicate",
    "invalid_request",
    "other"
]


class _NotProvided:
    pass


_NOT_PROVIDED = _NotProvided()


class UpdateTicketStatus(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        ticket_id: str,
        status: str | None | _NotProvided = _NOT_PROVIDED,
        assigned_employee_id: str | None | _NotProvided = _NOT_PROVIDED,
        priority: str | None | _NotProvided = _NOT_PROVIDED,
        resolution_id: str | None | _NotProvided = _NOT_PROVIDED,
        closure_reason: str | None | _NotProvided = _NOT_PROVIDED,
    ) -> str:
        # Validate enum parameters (allow None for optional fields)
        if status is not _NOT_PROVIDED and status is not None:
            validate_enum(status, ["new", "open", "pending_customer", "resolved", "closed"], "status")
        if priority is not _NOT_PROVIDED and priority is not None:
            validate_enum(priority, ["low", "normal", "high"], "priority")
        if closure_reason is not _NOT_PROVIDED and closure_reason is not None:
            validate_enum(closure_reason, VALID_CLOSURE_REASONS, "closure_reason")

        ticket_table = data.get("support_ticket")
        if not isinstance(ticket_table, dict):
            raise ValueError("Support ticket table not found in data")
        if ticket_id not in ticket_table:
            raise ValueError(f"Ticket {ticket_id} not found")

        ticket = ticket_table[ticket_id]
        if status is not _NOT_PROVIDED:
            ticket["status"] = status
        if assigned_employee_id is not _NOT_PROVIDED:
            ticket["assignedEmployeeId"] = assigned_employee_id
        if priority is not _NOT_PROVIDED:
            ticket["priority"] = priority
        if resolution_id is not _NOT_PROVIDED:
            ticket["resolutionId"] = resolution_id
        if closure_reason is not _NOT_PROVIDED:
            ticket["closureReason"] = closure_reason
        return json.loads(json.dumps(ticket))

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"updateTicketStatus",
                "description":"Update the status, priority, or assignment of a support ticket. Returns whether the update was successful.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "ticket_id": {
                            "type": "string",
                            "description": "The support ticket ID to update"
                        },
                        "status": {
                            "type": ["string", "null"],
                            "enum": ["new", "open", "pending_customer", "resolved", "closed", None],
                            "description": "The new status to set for the ticket"
                        },
                        "assigned_employee_id": {
                            "type": ["string", "null"],
                            "description": "Employee ID to assign the ticket to, or null to unassign"
                        },
                        "priority": {
                            "type": ["string", "null"],
                            "enum": ["low", "normal", "high", None],
                            "description": "The new priority to set for the ticket"
                        },
                        "resolution_id": {
                            "type": ["string", "null"],
                            "description": "Resolution ID to link to the ticket, or null to clear"
                        },
                        "closure_reason": {
                            "type": ["string", "null"],
                            "enum": VALID_CLOSURE_REASONS + [None],
                            "description": "Reason for closing the ticket, or null to clear"
                        }
                    },
                    "required":["ticket_id"]
                }
            }
        }
