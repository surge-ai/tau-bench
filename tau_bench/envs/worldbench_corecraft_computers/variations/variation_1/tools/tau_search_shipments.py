import json
import sqlite3
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data
from .tool_impls.search_shipments import searchShipments as _orig


class SearchShipments(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: Optional[str] = None,
        tracking_number: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
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

                from .tool_impls import search_shipments as search_shipments_module
                search_shipments_module.get_db_conn = lambda: conn

                result = _orig(
                    order_id=order_id,
                    tracking_number=tracking_number,
                    created_after=created_after,
                    created_before=created_before,
                    limit=limit,
                )
                # Convert Pydantic models to dicts for JSON serialization
                if isinstance(result, list):
                    result = [item.model_dump(mode='json') if hasattr(item, 'model_dump') else item for item in result]
                return json.dumps(result, default=str)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    search_shipments_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"searchShipments",
                "description":"Search for shipments with various filters. Returns an array of shipment records matching the criteria.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "order_id": {
                            "type": "string",
                            "description": "Order ID to filter by"
                        },
                        "tracking_number": {
                            "type": "string",
                            "description": "Tracking number to filter by"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter shipments created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter shipments created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
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
