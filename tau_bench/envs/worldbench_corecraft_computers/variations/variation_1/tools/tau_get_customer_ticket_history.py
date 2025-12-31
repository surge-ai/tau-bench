import json
import sqlite3
from typing import Any, Dict

from tau_bench.envs.tool import Tool
from tau_sqlite_utils import build_sqlite_from_data

from tool_impls.get_customer_ticket_history import getCustomerTicketHistory as _orig_getCustomerTicketHistory


class GetCustomerTicketHistory(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], **kwargs) -> str:
        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)

            # Monkeypatch get_db_conn() used by the legacy tool, if it imports from `utils`.
            try:
                import utils  # type: ignore
                utils.get_db_conn = lambda: conn  # type: ignore
            except Exception:
                pass

            result = _orig_getCustomerTicketHistory(**kwargs)
            return json.dumps(result)
        finally:
            conn.close()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "getCustomerTicketHistory",
                "description": "Get customer ticket history (legacy SQL-based tool wrapped for Tau).",
                "parameters": {
                    "type": "object",
                    "properties": {
        "customer_id": {
                "type": "string",
                "description": "The customer_id parameter"
        },
        "include_resolved": {
                "type": "string",
                "description": "Include resolved/closed tickets (default: true)"
        },
        "tkt_created_after": {
                "type": "string",
                "description": "Filter tickets created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
        },
        "tkt_created_before": {
                "type": "string",
                "description": "Filter tickets created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
        },
        "tkt_updated_after": {
                "type": "string",
                "description": "Filter tickets updated after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
        },
        "tkt_updated_before": {
                "type": "string",
                "description": "Filter tickets updated before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
        }
},
                    "required": ["customer_id"],
                },
            },
        }
