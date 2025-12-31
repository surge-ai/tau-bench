import json, sqlite3
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from tau_sqlite_utils import build_sqlite_from_data
from search_customers import searchCustomers as _orig

class SearchCustomers(Tool):
    @staticmethod
    def invoke(data: Dict[str,Any], **kwargs)->str:
        conn=sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn,data)
            try:
                import utils; utils.get_db_conn=lambda:conn
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
