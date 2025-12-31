# typed: ignore
import json, sqlite3
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from tau_sqlite_utils import build_sqlite_from_data
from search_shipments import searchShipments as _orig

class SearchShipments(Tool):
    @staticmethod
    def invoke(data: Dict[str,Any], **kwargs)->str:
        conn=sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn,data)
            try:
                import utils; utils.get_db_conn=lambda:conn
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
                "name":"searchShipments",
                "description":"Search shipments",
                "parameters":{
                    "type":"object",
                    "properties":{
          "order_id": {
                    "type": "string"
          },
          "tracking_number": {
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
