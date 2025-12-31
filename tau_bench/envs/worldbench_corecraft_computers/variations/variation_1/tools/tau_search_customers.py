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
            try:
                import utils; utils.get_db_conn=lambda:conn
                # Also update the reference in tool_impls since it has a direct import
                try:
                    tool_impls_module = importlib.import_module('.tool_impls.search_customers', package=__package__)
                    tool_impls_module.get_db_conn = lambda: conn
                except Exception: pass
            except Exception: pass
            res=_orig(**kwargs)
            return json.dumps(res)
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"searchCustomers",
                "description":"Search customers",
                "parameters":{
                    "type":"object",
                    "properties":{
          "customer_id": {
                    "type": "string"
          },
          "name": {
                    "type": "string"
          },
          "email": {
                    "type": "string"
          },
          "phone": {
                    "type": "string"
          },
          "loyalty_tier": {
                    "type": "string"
          },
          "address_text": {
                    "type": "string"
          },
          "created_after": {
                    "type": "string"
          },
          "created_before": {
                    "type": "string"
          },
          "limit": {
                    "type": "number"
          }
},
                    "required":[]
                }
            }
        }
