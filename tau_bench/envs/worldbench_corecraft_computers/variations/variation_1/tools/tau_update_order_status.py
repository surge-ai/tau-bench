import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class UpdateOrderStatus(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: str,
        status: str,
    ) -> str:
        updated = False

        order_table = data.get("order")
        if isinstance(order_table, dict) and order_id in order_table:
            order_table[order_id]["status"] = status
            updated = True

        return json.dumps({"updated": updated})

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"updateOrderStatus",
                "description":"Update the status of an order. Returns whether the update was successful.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "order_id": {
                            "type": "string",
                            "description": "The order ID to update"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "paid", "fulfilled", "cancelled", "backorder", "refunded", "partially_refunded", "refund_requested"],
                            "description": "The new status to set for the order"
                        }
                    },
                    "required":["order_id", "status"]
                }
            }
        }
