# typed: ignore
import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class UpdateTicketStatus(Tool):
    @staticmethod
    def invoke(data: Dict[str,Any], **kwargs)->str:
        ticket_id = kwargs.get("ticket_id")
        new_status = kwargs.get("status")
        updated = False

        for ticket in data.get("tickets", []):
            if ticket.get("id") == ticket_id:
                ticket["status"] = new_status
                updated = True
                break

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
