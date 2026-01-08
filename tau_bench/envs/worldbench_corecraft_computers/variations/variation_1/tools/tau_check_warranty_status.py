import json
import sqlite3
import importlib
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data

# Import the original function (kept as-is)
from .tool_impls.check_warranty_status import checkWarrantyStatus as _orig_checkWarrantyStatus


class CheckWarrantyStatus(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: Optional[str] = None,
        product_id: Optional[str] = None,
        purchase_date: Optional[str] = None,
        current_date: Optional[str] = None,
    ) -> str:
        # Build an in-memory SQLite DB from `data` for read-only querying.
        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)

            # Patch get_db_conn in both utils and the module that imported it
            try:
                from .tool_impls import utils as tool_utils
                original_get_db_conn = tool_utils.get_db_conn
                tool_utils.get_db_conn = lambda: conn
                
                from .tool_impls import check_warranty_status as check_warranty_status_module
                check_warranty_status_module.get_db_conn = lambda: conn

                result = _orig_checkWarrantyStatus(
                    order_id=order_id,
                    product_id=product_id,
                    purchase_date=purchase_date,
                    current_date=current_date,
                )
                return json.dumps(result)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    check_warranty_status_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "checkWarrantyStatus",
                "description": "Check whether a product/order is still under warranty based on order details and product warranty terms. Returns is_under_warranty (boolean), warranty_end_date (YYYY-MM-DD string), and days_remaining (number). Either order_id or product_id must be provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID to check warranty status for. If provided, purchase date is derived from the order's creation date."
                        },
                        "product_id": {
                            "type": "string",
                            "description": "The product ID to check warranty for. Can be used alone (with purchase_date) or combined with order_id to check a specific product in an order."
                        },
                        "purchase_date": {
                            "type": "string",
                            "description": "The purchase date (ISO 8601 format with UTC timezone, e.g., \"2025-01-15T00:00:00Z\"). Required when using product_id without order_id."
                        },
                        "current_date": {
                            "type": "string",
                            "description": "The current date for warranty calculation (ISO 8601 format with UTC timezone, e.g., \"2025-09-08T00:00:00Z\"). Defaults to September 8, 2025 if not provided."
                        }
                    },
                    "required": [],
                },
            },
        }
