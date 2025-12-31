import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class UpdatePaymentStatus(Tool):
    @staticmethod
    def invoke(data: Dict[str,Any], **kwargs)->str:
        payment_id = kwargs.get("payment_id")
        new_status = kwargs.get("status")
        updated = False

        for payment in data.get("payments", []):
            if payment.get("id") == payment_id:
                payment["status"] = new_status
                updated = True
                break

        return json.dumps({"updated": updated})

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"updatePaymentStatus",
                "description":"Update payment status",
                "parameters":{
                    "type":"object",
                    "properties":{
          "payment_id": {
                    "type": "string"
          },
          "status": {
                    "type": "string"
          },
          "failure_reason": {
                    "type": "string"
          }
},
                    "required":["payment_id", "status"]
                }
            }
        }
