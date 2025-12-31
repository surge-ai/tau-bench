import json
import sqlite3
from typing import Any, Dict

from tau_bench.envs.tool import Tool
from tau_sqlite_utils import build_sqlite_from_data

from tool_impls.get_product import getProduct as _orig_getProduct


class GetProduct(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], **kwargs) -> str:
        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)
            try:
                import utils  # type: ignore
                utils.get_db_conn = lambda: conn  # type: ignore
                # Also update the reference in tool_impls since it has a direct import
                try:
                    import tool_impls.get_product as tool_impls_module  # type: ignore
                    tool_impls_module.get_db_conn = lambda: conn  # type: ignore
                except Exception:
                    pass
            except Exception:
                pass

            result = _orig_getProduct(**kwargs)
            return json.dumps(result)
        finally:
            conn.close()

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "getProduct",
                "description": "Get product details (legacy SQL tool wrapped for Tau).",
                "parameters": {
                    "type": "object",
                    "properties": {
        "product_id": {
                "type": "string",
                "description": "The product_id parameter"
        }
},
                    "required": ["product_id"],
                },
            },
        }
