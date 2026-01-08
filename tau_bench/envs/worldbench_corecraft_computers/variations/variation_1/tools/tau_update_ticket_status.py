import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class UpdateTicketStatus(Tool):
    @staticmethod
    def invoke(data: Dict[str,Any], **kwargs)->str:
        ticket_id = kwargs.get("ticket_id")
        new_status = kwargs.get("status")
        assigned_employee_id = kwargs.get("assigned_employee_id")
        priority = kwargs.get("priority")
        updated = False

        ticket_table = data.get("support_ticket")
        if isinstance(ticket_table, dict) and ticket_id in ticket_table:
            ticket = ticket_table[ticket_id]
            if new_status is not None:
                ticket["status"] = new_status
            if assigned_employee_id is not None:
                ticket["assignedEmployeeId"] = assigned_employee_id
            if priority is not None:
                ticket["priority"] = priority
            updated = True

        return json.dumps({"updated": updated})

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
                            "type": "string",
                            "enum": ["new", "open", "pending_customer", "resolved", "closed"],
                            "description": "The new status to set for the ticket"
                        },
                        "assigned_employee_id": {
                            "type": "string",
                            "description": "Employee ID to assign the ticket to"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "normal", "high"],
                            "description": "The new priority to set for the ticket"
                        }
                    },
                    "required":["ticket_id"]
                }
            }
        }
