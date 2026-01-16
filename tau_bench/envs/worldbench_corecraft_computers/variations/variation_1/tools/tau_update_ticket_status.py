import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

from .data_utils import validate_enum


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
    ) -> str:
        # Validate enum parameters (allow None for optional fields)
        if status is not _NOT_PROVIDED and status is not None:
            error = validate_enum(status, ["new", "open", "pending_customer", "resolved", "closed"], "status")
            if error:
                return error
        if priority is not _NOT_PROVIDED and priority is not None:
            error = validate_enum(priority, ["low", "normal", "high"], "priority")
            if error:
                return error

        ticket_table = data.get("support_ticket")
        if not isinstance(ticket_table, dict):
            return json.loads(json.dumps({"error": "Support ticket table not found in data"}))
        if ticket_id not in ticket_table:
            return json.loads(json.dumps({"error": f"Ticket {ticket_id} not found"}))

        ticket = ticket_table[ticket_id]
        if status is not _NOT_PROVIDED:
            ticket["status"] = status
        if assigned_employee_id is not _NOT_PROVIDED:
            ticket["assignedEmployeeId"] = assigned_employee_id
        if priority is not _NOT_PROVIDED:
            ticket["priority"] = priority
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
                        }
                    },
                    "required":["ticket_id"]
                }
            }
        }
