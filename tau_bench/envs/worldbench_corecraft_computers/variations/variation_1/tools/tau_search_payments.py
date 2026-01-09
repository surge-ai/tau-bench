import json
import sqlite3
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data
from .tool_impls.search_payments import searchPayments as _orig


class SearchPayments(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        processed_after: Optional[str] = None,
        processed_before: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)
            # Patch get_db_conn in both utils and the module that imported it
            try:
                from .tool_impls import utils as tool_utils
                original_get_db_conn = tool_utils.get_db_conn
                tool_utils.get_db_conn = lambda: conn

                from .tool_impls import search_payments as search_payments_module
                search_payments_module.get_db_conn = lambda: conn

                result = _orig(
                    order_id=order_id,
                    status=status,
                    created_after=created_after,
                    created_before=created_before,
                    processed_after=processed_after,
                    processed_before=processed_before,
                    limit=limit,
                )
                # Convert Pydantic models to dicts for JSON serialization
                if isinstance(result, list):
                    result = [item.model_dump(mode='json') if hasattr(item, 'model_dump') else item for item in result]
                return json.dumps(result, default=str)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    search_payments_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"searchPayments",
                "description":"Search for payments with various filters. Returns an array of payment records matching the criteria.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "order_id": {
                            "type": "string",
                            "description": "Order ID to filter by"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "authorized", "captured", "failed", "refunded", "disputed", "voided", "completed"],
                            "description": "Payment status to filter by"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter payments created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter payments created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        },
                        "processed_after": {
                            "type": "string",
                            "description": "Filter payments processed after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "processed_before": {
                            "type": "string",
                            "description": "Filter payments processed before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default 50, max 200)"
                        }
                    },
                    "required":[]
                }
            }
        }
