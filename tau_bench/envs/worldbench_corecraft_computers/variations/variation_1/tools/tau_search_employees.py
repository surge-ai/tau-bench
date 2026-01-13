import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_entity_json_fields,
    matches_json_text_search,
    apply_limit,
    validate_enum,
)

DEPARTMENTS = ["operations", "order_processing", "engineering", "help_desk", "it_systems", "product_management", "finance", "hr", "recruitment", "support"]
PERMISSIONS = ["issue_refund", "edit_order", "cancel_order", "escalate", "kb_edit", "policy_override"]


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
        validate_enum(department, DEPARTMENTS, "department")
        validate_enum(has_permission, PERMISSIONS, "has_permission")

        results: List[Dict[str, Any]] = []

        for row in iter_entities(data, "employee"):
            # Exact employee_id match
            if employee_id and row.get("id") != employee_id:
                continue
            # Exact department match
            if department and row.get("department") != department:
                continue
            # Partial name match (case insensitive)
            if name:
                row_name = row.get("name", "")
                if name.lower() not in row_name.lower():
                    continue
            # Partial role/title match (case insensitive)
            if role:
                row_title = row.get("title", "")
                if role.lower() not in row_title.lower():
                    continue
            # Permission search in JSON field
            if has_permission and not matches_json_text_search(row, "permissions", has_permission):
                continue

            # Parse JSON fields
            result_row = parse_entity_json_fields(row, ["permissions"])
            results.append(result_row)

        # Sort by name ASC, then by id ASC
        results.sort(key=lambda e: (e.get("name", ""), e.get("id", "")))

        # Apply limit
        results = apply_limit(results, limit)

        return json.dumps(results, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchEmployees",
                "description": "Search for employees with various filters. Returns an array of employee records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
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
                    "required": []
                }
            }
        }
