import json, sqlite3
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from tau_sqlite_utils import build_sqlite_from_data
from tool_impls.search_knowledge_base import searchKnowledgeBase as _orig

class SearchKnowledgeBase(Tool):
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
                "name":"searchKnowledgeBase",
                "description":"Search knowledge base",
                "parameters":{
                    "type":"object",
                    "properties":{
          "text": {
                    "type": "string"
          },
          "tags": {
                    "type": "array",
                    "items": {
                              "type": "string"
                    }
          },
          "created_after": {
                    "type": "string"
          },
          "created_before": {
                    "type": "string"
          },
          "updated_after": {
                    "type": "string"
          },
          "updated_before": {
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
