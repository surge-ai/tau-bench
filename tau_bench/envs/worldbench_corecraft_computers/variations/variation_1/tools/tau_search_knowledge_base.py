import json, sqlite3
import importlib
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data
from .tool_impls.search_knowledge_base import searchKnowledgeBase as _orig

class SearchKnowledgeBase(Tool):
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
                
                from .tool_impls import search_knowledge_base as search_knowledge_base_module
                search_knowledge_base_module.get_db_conn = lambda: conn
                
                result = _orig(**kwargs)
                # Convert Pydantic models to dicts for JSON serialization
                if isinstance(result, list):
                    result = [item.model_dump(mode='json') if hasattr(item, 'model_dump') else item for item in result]
                return json.dumps(result, default=str)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    search_knowledge_base_module.get_db_conn = original_get_db_conn
                except:
                    pass
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
