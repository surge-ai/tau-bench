# typed: ignore
import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class UpdateOrderStatus(Tool):
    @staticmethod
    def invoke(data: Dict[str,Any], **kwargs)->str:
        # WRITE TOOL: mutate data in-place
        order_id = kwargs.get("order_id")
        new_status = kwargs.get("status")
        updated = False

        for order in data.get("orders", []):
            if order.get("id") == order_id:
                order["status"] = new_status
                updated = True
                break

        return json.dumps({"updated": updated})

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"updateOrderStatus",
                "description":"Update order status",
                "parameters":{
                    "type":"object",
                    "properties":{
          "order_id": {
                    "type": "string"
          },
          "status": {
                    "type": "string"
          }
},
                    "required":["order_id", "status"]
                }
            }
        }
