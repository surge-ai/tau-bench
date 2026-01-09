import json, sqlite3
from typing import Any, Dict, Optional
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
                "description":"Search for knowledge base articles with various filters. Returns an array of article records matching the criteria.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "text": {
                            "type": "string",
                            "description": "Text to search in title and body"
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Tags to filter by"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter articles created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter articles created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "updated_after": {
                            "type": "string",
                            "description": "Filter articles updated after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "updated_before": {
                            "type": "string",
                            "description": "Filter articles updated before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default 50, max 200)"
                        }
                    },
                    "required":[]
                }
            }
        }
