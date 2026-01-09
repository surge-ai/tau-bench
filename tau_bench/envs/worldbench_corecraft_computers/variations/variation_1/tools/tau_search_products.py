import json, sqlite3
import importlib
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data
from .tool_impls.search_products import searchProducts as _orig

class SearchProducts(Tool):
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
                
                from .tool_impls import search_products as search_products_module
                search_products_module.get_db_conn = lambda: conn
                
                result = _orig(**kwargs)
                # Convert Pydantic models to dicts for JSON serialization
                if isinstance(result, list):
                    result = [item.model_dump(mode='json') if hasattr(item, 'model_dump') else item for item in result]
                return json.dumps(result, default=str)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    search_products_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"searchProducts",
                "description":"Search for products with various filters. Returns an array of product records matching the criteria.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "category": {
                            "type": "string",
                            "enum": ["cpu", "motherboard", "gpu", "memory", "storage", "psu", "case", "cooling", "prebuilt", "workstation", "monitor", "keyboard", "mouse", "headset", "networking", "cable", "accessory", "bundle"],
                            "description": "Product category to filter by"
                        },
                        "brand": {
                            "type": "string",
                            "description": "Product brand name to filter by"
                        },
                        "min_price": {
                            "type": "number",
                            "description": "Minimum price filter"
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price filter"
                        },
                        "price": {
                            "type": "number",
                            "description": "Exact price filter"
                        },
                        "inStockOnly": {
                            "type": "string",
                            "description": "Set to any non-empty value (e.g., \"true\") to only return products with inventory > 0"
                        },
                        "minStock": {
                            "type": "number",
                            "description": "Minimum stock level filter"
                        },
                        "maxStock": {
                            "type": "number",
                            "description": "Maximum stock level filter"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text search across name, brand, and SKU"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default 50, max 200)"
                        },
                        "product_id": {
                            "type": "string",
                            "description": "Exact product ID filter"
                        }
                    },
                    "required":[]
                }
            }
        }
