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
            # Patch get_db_conn in both utils and the module that imported it
            try:
                from .tool_impls import utils as tool_utils
                original_get_db_conn = tool_utils.get_db_conn
                tool_utils.get_db_conn = lambda: conn
                
                from .tool_impls import validate_build_compatibility as validate_build_compatibility_module
                validate_build_compatibility_module.get_db_conn = lambda: conn
                
                result = _orig(**kwargs)
                return json.dumps(result)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    validate_build_compatibility_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"validateBuildCompatibility",
                "description":"Validate PC build compatibility for a list of product IDs. Checks CPU-motherboard socket compatibility, motherboard-case form factor compatibility, memory type and speed compatibility, memory slot count, SATA port count, GPU and cooler clearance, and PSU wattage requirements. Returns is_compatible (boolean), errors (list of incompatibility issues), and warnings (list of potential concerns).",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "product_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of product IDs to check for compatibility"
                        }
                    },
                    "required":["product_ids"]
                }
            }
        }
