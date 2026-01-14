import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

from .data_utils import validate_enum


class UpdateOrderStatus(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: str,
        status: str,
    ) -> str:
        # Validate enum parameters
        validate_enum(status, ["pending", "paid", "fulfilled", "cancelled", "backorder", "refunded", "partially_refunded"], "status")

        order_table = data.get("order")
        if not isinstance(order_table, dict):
            raise ValueError("Order table not found in data")
        if order_id not in order_table:
            raise ValueError(f"Order {order_id} not found")

        order_table[order_id]["status"] = status
        return json.loads(json.dumps(order_table[order_id]))

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
