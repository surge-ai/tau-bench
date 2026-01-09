import json
import sqlite3
import importlib
from typing import Any, Dict

from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data

from .tool_impls.get_customer_ticket_history import getCustomerTicketHistory as _orig_getCustomerTicketHistory


class GetCustomerTicketHistory(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], **kwargs) -> str:
        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)
            # Patch get_db_conn in both utils and the module that imported it
            try:
                from .tool_impls import utils as tool_utils
                original_get_db_conn = tool_utils.get_db_conn
                tool_utils.get_db_conn = lambda: conn
                
                from .tool_impls import get_customer_ticket_history as get_customer_ticket_history_module
                get_customer_ticket_history_module.get_db_conn = lambda: conn
                
                result = _orig_getCustomerTicketHistory(**kwargs)
                return json.dumps(result)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    get_customer_ticket_history_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "getCustomerTicketHistory",
                "description": "Get a customer's support ticket history including escalations and resolutions. Returns an object with tickets (array of support tickets), escalations (array of escalation records), and resolutions (array of resolution records).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer ID to retrieve ticket history for"
                        },
                        "include_resolved": {
                            "type": "string",
                            "description": "Include resolved/closed tickets. Set to \"false\" to exclude them (default: \"true\")"
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
