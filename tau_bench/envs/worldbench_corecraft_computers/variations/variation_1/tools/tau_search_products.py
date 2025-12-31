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
            try:
                import utils; utils.get_db_conn=lambda:conn
                # Also update the reference in tool_impls since it has a direct import
                try:
                    tool_impls_module = importlib.import_module('.tool_impls.search_products', package=__package__)
                    tool_impls_module.get_db_conn = lambda: conn
                except Exception: pass
            except Exception:
                pass
            return json.dumps(_orig(**kwargs))
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"searchProducts",
                "description":"Search products",
                "parameters":{
                    "type":"object",
                    "properties":{
          "category": {
                    "type": "string"
          },
          "brand": {
                    "type": "string"
          },
          "min_price": {
                    "type": "number"
          },
          "max_price": {
                    "type": "number"
          },
          "price": {
                    "type": "number"
          },
          "inStockOnly": {
                    "type": "string"
          },
          "minStock": {
                    "type": "number"
          },
          "maxStock": {
                    "type": "number"
          },
          "text": {
                    "type": "string"
          },
          "limit": {
                    "type": "number"
          },
          "product_id": {
                    "type": "string"
          }
},
                    "required":[]
                }
            }
        }
