# typed: ignore
# Tau Bench read tool: search_orders

from typing import Any, Dict, List, Optional
from tau_bench.envs.tool import Tool


def _iter_orders(data: Dict[str, Any]):
    for key in ("orders", "Orders", "Order"):
        table = data.get(key)
        if isinstance(table, dict):
            for row in table.values():
                if isinstance(row, dict):
                    yield row
        elif isinstance(table, list):
            for row in table:
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
                "description": "Search orders by id, customer, or status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "customer_id": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
            },
        }
