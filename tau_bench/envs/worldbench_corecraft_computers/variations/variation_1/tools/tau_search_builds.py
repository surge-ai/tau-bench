# typed: ignore
# Auto-converted Tau Bench read-tool wrapper
# Source: search_builds.py::searchBuilds

import json
import sqlite3
from typing import Any, Dict

from tau_bench.envs.tool import Tool
from tau_sqlite_utils import build_sqlite_from_data

from search_builds import searchBuilds as _orig_searchBuilds


class SearchBuilds(Tool):
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

            result = _orig_searchBuilds(**kwargs)
            return json.dumps(result)
        finally:
            conn.close()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchBuilds",
                "description": "Search builds (legacy SQL tool wrapped for Tau).",
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
