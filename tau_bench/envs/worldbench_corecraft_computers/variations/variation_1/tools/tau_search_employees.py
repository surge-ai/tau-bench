# typed: ignore
import json, sqlite3
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from tau_sqlite_utils import build_sqlite_from_data
from search_employees import searchEmployees as _orig

class SearchEmployees(Tool):
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
                "name":"searchEmployees",
                "description":"Search employees",
                "parameters":{
                    "type":"object",
                    "properties":{
          "employee_id": {
                    "type": "string"
          },
          "name": {
                    "type": "string"
          },
          "department": {
                    "type": "string"
          },
          "role": {
                    "type": "string"
          },
          "has_permission": {
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
