import json
import sqlite3
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool
from .tau_sqlite_utils import build_sqlite_from_data
from .tool_impls.search_employees import searchEmployees as _orig


class SearchEmployees(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        employee_id: Optional[str] = None,
        name: Optional[str] = None,
        department: Optional[str] = None,
        role: Optional[str] = None,
        has_permission: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)
            # Patch get_db_conn in both utils and the module that imported it
            try:
                from .tool_impls import utils as tool_utils
                original_get_db_conn = tool_utils.get_db_conn
                tool_utils.get_db_conn = lambda: conn

                from .tool_impls import search_employees as search_employees_module
                search_employees_module.get_db_conn = lambda: conn

                result = _orig(
                    employee_id=employee_id,
                    name=name,
                    department=department,
                    role=role,
                    has_permission=has_permission,
                    limit=limit,
                )
                # Convert Pydantic models to dicts for JSON serialization
                if isinstance(result, list):
                    result = [item.model_dump(mode='json') if hasattr(item, 'model_dump') else item for item in result]
                return json.dumps(result, default=str)
            finally:
                try:
                    tool_utils.get_db_conn = original_get_db_conn
                    search_employees_module.get_db_conn = original_get_db_conn
                except:
                    pass
        finally:
            conn.close()

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"searchEmployees",
                "description":"Search for employees with various filters. Returns an array of employee records matching the criteria.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "employee_id": {
                            "type": "string",
                            "description": "Exact employee ID match"
                        },
                        "name": {
                            "type": "string",
                            "description": "Partial name search (case insensitive)"
                        },
                        "department": {
                            "type": "string",
                            "enum": ["operations", "order_processing", "engineering", "help_desk", "it_systems", "product_management", "finance", "hr", "recruitment", "support"],
                            "description": "Department to filter by"
                        },
                        "role": {
                            "type": "string",
                            "description": "Role/title to search for"
                        },
                        "has_permission": {
                            "type": "string",
                            "enum": ["issue_refund", "edit_order", "cancel_order", "escalate", "kb_edit", "policy_override"],
                            "description": "Permission to filter by"
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
