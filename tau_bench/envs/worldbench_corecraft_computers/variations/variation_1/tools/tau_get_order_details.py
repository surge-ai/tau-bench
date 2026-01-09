import json
import sqlite3
from typing import Any, Dict

from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data

from .tool_impls.get_order_details import getOrderDetails as _orig_getOrderDetails


class GetOrderDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], **kwargs) -> str:
        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)
            # Patch get_db_conn in both utils and the module that imported it
            try:
                # Patch in utils module
                from .tool_impls import utils as tool_utils
                original_get_db_conn = tool_utils.get_db_conn
                tool_utils.get_db_conn = lambda: conn

                # Patch in get_order_details module (it does "from .utils import get_db_conn")
                from .tool_impls import get_order_details as get_order_details_module
                get_order_details_module.get_db_conn = lambda: conn

                result = _orig_getOrderDetails(**kwargs)
                return json.dumps(result)
            finally:
                # Restore original function
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    get_order_details_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "getOrderDetails",
                "description": "Get comprehensive order details including the order itself, associated payment, shipment, customer info, and related support tickets. Returns an object with order, payment, shipment, customer, and tickets fields.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID to retrieve details for"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter related objects (payments, shipments, tickets) to those created before this date, inclusive (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        }
                    },
                    "required": ["order_id"],
                },
            },
        }
