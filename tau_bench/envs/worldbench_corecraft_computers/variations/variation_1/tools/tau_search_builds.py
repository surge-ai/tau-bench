import json
import sqlite3
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data

from .tool_impls.search_builds import searchBuilds as _orig_searchBuilds


class SearchBuilds(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        name: Optional[str] = None,
        customer_id: Optional[str] = None,
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

                from .tool_impls import search_builds as search_builds_module
                search_builds_module.get_db_conn = lambda: conn

                result = _orig_searchBuilds(
                    name=name,
                    customer_id=customer_id,
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
                    search_builds_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchBuilds",
                "description": "Search for PC builds with various filters. Returns an array of build records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
        "name": {
                "type": "string",
                "description": "Build name to search for"
        },
        "customer_id": {
                "type": "string",
                "description": "Customer ID to filter by"
        },
        "created_after": {
                "type": "string",
                "description": "Filter builds created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
        },
        "created_before": {
                "type": "string",
                "description": "Filter builds created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
        },
        "limit": {
                "type": "number",
                "description": "Maximum number of results (default 50, max 200)"
        }
},
                    "required": [],
                },
            },
        }
