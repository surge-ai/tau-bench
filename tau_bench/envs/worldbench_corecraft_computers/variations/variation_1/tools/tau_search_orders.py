from typing import Any, Dict, List, Optional
from tau_bench.envs.tool import Tool


def _iter_orders(data: Dict[str, Any]):
    order_table = data.get("order")
    if isinstance(order_table, dict):
        for row in order_table.values():
            if isinstance(row, dict):
                yield row


class SearchOrders(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        results: List[Dict[str, Any]] = []

        for row in _iter_orders(data):
            if order_id and row.get("id") != order_id:
                continue
            if customer_id and row.get("customerId") != customer_id:
                continue
            if status and row.get("status") != status:
                continue
            results.append(row)

        return str(results)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "search_orders",
                "description": "Search for orders with various filters. Returns an array of order records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Exact order ID to find"
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID to filter by"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "paid", "fulfilled", "cancelled", "backorder", "refunded", "partially_refunded", "refund_requested"],
                            "description": "Order status to filter by"
                        },
                    },
                },
            },
        }
