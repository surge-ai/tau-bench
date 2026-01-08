import json
import sqlite3
import importlib
from typing import Any, Dict

from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data

from .tool_impls.get_product import getProduct as _orig_getProduct


class GetProduct(Tool):
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
                
                from .tool_impls import get_product as get_product_module
                get_product_module.get_db_conn = lambda: conn
                
                result = _orig_getProduct(**kwargs)
                return json.dumps(result)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    get_product_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "getProduct",
                "description": "Get detailed information about a product by its ID. Returns the full product record including category, SKU, name, brand, price, inventory, specs, and warranty information. Returns null if the product is not found.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "The product ID to retrieve"
                        }
                    },
                    "required": ["product_id"],
                },
            },
        }
