import json, sqlite3
import importlib
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data
from .tool_impls.search_customers import searchCustomers as _orig

class SearchCustomers(Tool):
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
                
                from .tool_impls import search_customers as search_customers_module
                search_customers_module.get_db_conn = lambda: conn
                
                res = _orig(**kwargs)
                # Convert Pydantic models to dicts for JSON serialization
                if isinstance(res, list):
                    res = [item.model_dump(mode='json') if hasattr(item, 'model_dump') else item for item in res]
                return json.dumps(res, default=str)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    search_customers_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"searchCustomers",
                "description":"Search for customers with various filters. Returns an array of customer records matching the criteria.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "customer_id": {
                            "type": "string",
                            "description": "Exact customer ID match"
                        },
                        "name": {
                            "type": "string",
                            "description": "Partial name search (case insensitive)"
                        },
                        "email": {
                            "type": "string",
                            "description": "Exact email address match"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Exact phone number match"
                        },
                        "loyalty_tier": {
                            "type": "string",
                            "enum": ["none", "silver", "gold", "platinum"],
                            "description": "Customer loyalty tier to filter by"
                        },
                        "address_text": {
                            "type": "string",
                            "description": "Text search across all address fields (city, region, postal code, street address, etc.)"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter customers created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter customers created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
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
