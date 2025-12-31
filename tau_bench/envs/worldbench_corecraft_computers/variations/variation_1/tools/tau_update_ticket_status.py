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
                "description":"Update ticket status",
                "parameters":{
                    "type":"object",
                    "properties":{
          "ticket_id": {
                    "type": "string"
          },
          "status": {
                    "type": "string"
          },
          "assigned_employee_id": {
                    "type": "string"
          },
          "priority": {
                    "type": "string"
          }
},
                    "required":["ticket_id"]
                }
            }
        }
