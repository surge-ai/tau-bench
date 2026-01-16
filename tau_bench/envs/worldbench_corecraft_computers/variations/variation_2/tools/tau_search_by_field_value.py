import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import (
        get_entity_data_key,
        VALID_ENTITY_TYPES,
        validate_enum_value,
        get_valid_fields_for_entity_type,
    )
except ImportError:
    from utils import (
        get_entity_data_key,
        VALID_ENTITY_TYPES,
        validate_enum_value,
        get_valid_fields_for_entity_type,
    )


class SearchByFieldValue(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        field_name: str,
        field_value: Any,
    ) -> str:
        """Generic search: find all entities where field equals value."""
        # Validate entity_type enum
        error_msg = validate_enum_value(entity_type, VALID_ENTITY_TYPES, "entity_type")
        if error_msg:
            return json.loads(json.dumps({"error": error_msg}))

        data_key = get_entity_data_key(entity_type)
        if not data_key:
            return json.loads(json.dumps({"error": f"Unknown entity type: {entity_type}"}))

        # Validate field_name is a valid field for this entity type
        valid_fields = get_valid_fields_for_entity_type(entity_type)
        if valid_fields is not None and field_name not in valid_fields:
            sorted_valid_fields = sorted(valid_fields)
            return json.loads(json.dumps({
                "error": f"Invalid field name '{field_name}' for entity type '{entity_type}'",
                "field_name": field_name,
                "entity_type": entity_type,
                "valid_fields": sorted_valid_fields,
                "suggestion": f"Use get_entity_schema tool with entity_type='{entity_type}' to see all valid fields and their types.",
            }))

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict):
            return json.loads(json.dumps({"results": [], "count": 0}))

        results = []

        for entity in entity_table.values():
            if not isinstance(entity, dict):
                continue

            entity_field_value = entity.get(field_name)

            # Handle string comparison (case-insensitive)
            if isinstance(field_value, str) and isinstance(entity_field_value, str):
                if entity_field_value.lower() == field_value.lower():
                    results.append(entity)
            else:
                # Exact match for other types
                if entity_field_value == field_value:
                    results.append(entity)

        return json.loads(json.dumps({
            "entity_type": entity_type,
            "field_name": field_name,
            "field_value": field_value,
            "results": results,
            "count": len(results),
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "search_by_field_value",
                "description": "Generic search: find all entities of a type where a specific field equals a value. Case-insensitive for strings. **Use camelCase for field names (e.g., 'customerId' not 'customer_id'). Use get_entity_schema to discover valid field names.**",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity.",
                            "enum": VALID_ENTITY_TYPES,
                        },
                        "field_name": {
                            "type": "string",
                            "description": "Name of the field to search (e.g., 'status', 'customerId', 'priority').",
                        },
                        "field_value": {
                            "description": "Value to match (string, number, or boolean).",
                        },
                    },
                    "required": ["entity_type", "field_name", "field_value"],
                },
            },
        }
