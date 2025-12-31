import json, sqlite3
import importlib
from typing import Any, Dict
from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data
from .tool_impls.validate_build_compatibility import validateBuildCompatibility as _orig

class ValidateBuildCompatibility(Tool):
    @staticmethod
    def invoke(data: Dict[str,Any], **kwargs)->str:
        # Read/compute tool: build in-memory DB for consistency
        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)
            try:
                import utils; utils.get_db_conn=lambda:conn
                # Also update the reference in tool_impls since it has a direct import
                try:
                    tool_impls_module = importlib.import_module('.tool_impls.validate_build_compatibility', package=__package__)
                    tool_impls_module.get_db_conn = lambda: conn
                except Exception:
                    pass
            except Exception:
                pass
            result = _orig(**kwargs)
            return json.dumps(result)
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"validateBuildCompatibility",
                "description":"Validate build compatibility",
                "parameters":{
                    "type":"object",
                    "properties":{
          "product_ids": {
                    "type": "array",
                    "items": {
                              "type": "string"
                    }
          }
},
                    "required":["product_ids"]
                }
            }
        }
