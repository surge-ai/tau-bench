import json, sqlite3
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from tau_sqlite_utils import build_sqlite_from_data
from tool_impls.search_tickets import searchTickets as _orig

class SearchTickets(Tool):
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
                "name":"searchTickets",
                "description":"Search tickets",
                "parameters":{
                    "type":"object",
                    "properties":{
          "ticket_id": {
                    "type": "string"
          },
          "customer_id": {
                    "type": "string"
          },
          "assigned_employee_id": {
                    "type": "string"
          },
          "status": {
                    "type": "string"
          },
          "priority": {
                    "type": "string"
          },
          "ticket_type": {
                    "type": "string"
          },
          "text": {
                    "type": "string"
          },
          "created_after": {
                    "type": "string"
          },
          "created_before": {
                    "type": "string"
          },
          "resolved_after": {
                    "type": "string"
          },
          "resolved_before": {
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
