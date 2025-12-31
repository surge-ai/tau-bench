import json
import sqlite3
from typing import Any, Dict

from tau_bench.envs.tool import Tool
from tau_sqlite_utils import build_sqlite_from_data

from get_order_details import getOrderDetails as _orig_getOrderDetails


class GetOrderDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], **kwargs) -> str:
        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)
            try:
                import utils  # type: ignore
                utils.get_db_conn = lambda: conn  # type: ignore
            except Exception:
                pass

            result = _orig_getOrderDetails(**kwargs)
            return json.dumps(result)
        finally:
            conn.close()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "getOrderDetails",
                "description": "Get order details (legacy SQL tool wrapped for Tau).",
                "parameters": {
                    "type": "object",
                    "properties": {
        "order_id": {
                "type": "string",
                "description": "The order_id parameter"
        },
        "created_before": {
                "type": "string",
                "description": "Filter order details to objects created before this date, inclusive (ISO 8601 format with UTC timezone, e.g., '2025-09-01T00:00:00Z')"
        }
},
                    "required": ["order_id"],
                },
            },
        }
