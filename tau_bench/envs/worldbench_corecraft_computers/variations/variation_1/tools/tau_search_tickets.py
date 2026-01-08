import json, sqlite3
import importlib
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data
from .tool_impls.search_tickets import searchTickets as _orig

class SearchTickets(Tool):
    @staticmethod
    def invoke(data: Dict[str,Any], **kwargs)->str:
        conn=sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn,data)
            # Patch get_db_conn in both utils and the module that imported it
            try:
                from .tool_impls import utils as tool_utils
                original_get_db_conn = tool_utils.get_db_conn
                tool_utils.get_db_conn = lambda: conn
                
                from .tool_impls import search_tickets as search_tickets_module
                search_tickets_module.get_db_conn = lambda: conn
                
                result = _orig(**kwargs)
                # Convert Pydantic models to dicts for JSON serialization
                if isinstance(result, list):
                    result = [item.model_dump(mode='json') if hasattr(item, 'model_dump') else item for item in result]
                return json.dumps(result, default=str)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    search_tickets_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"searchTickets",
                "description":"Search for support tickets with various filters. Returns an array of support ticket records matching the criteria, sorted by priority (high to low) and then by creation date (newest first).",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "ticket_id": {
                            "type": "string",
                            "description": "Specific ticket ID to find"
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID to filter by"
                        },
                        "assigned_employee_id": {
                            "type": "string",
                            "description": "Employee ID to filter by"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["new", "open", "pending_customer", "resolved", "closed"],
                            "description": "Ticket status to filter by"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "normal", "high"],
                            "description": "Ticket priority to filter by"
                        },
                        "ticket_type": {
                            "type": "string",
                            "enum": ["return", "troubleshooting", "recommendation", "order_issue", "shipping", "billing", "other"],
                            "description": "Ticket type to filter by"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to search in subject and body. Searches for exact matches (case insensitive)."
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter tickets created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter tickets created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        },
                        "resolved_after": {
                            "type": "string",
                            "description": "Filter tickets resolved after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "resolved_before": {
                            "type": "string",
                            "description": "Filter tickets resolved before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
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
