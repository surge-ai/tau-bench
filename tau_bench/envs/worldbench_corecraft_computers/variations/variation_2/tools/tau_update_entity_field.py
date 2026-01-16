import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import (
        get_entity_data_key,
        VALID_ENTITY_TYPES,
        validate_enum_value,
        get_valid_fields_for_entity_type,
        get_now_iso_from_data,
    )
except ImportError:
    from utils import (
        get_entity_data_key,
        VALID_ENTITY_TYPES,
        validate_enum_value,
        get_valid_fields_for_entity_type,
        get_now_iso_from_data,
    )


class UpdateEntityField(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        entity_id: str,
        field_name: str,
        field_value: Any,
    ) -> str:
        """Generic field updater: update any field on any entity type."""
        # Validate entity_type enum
        error_msg = validate_enum_value(entity_type, VALID_ENTITY_TYPES, "entity_type")
        if error_msg:
            return json.loads(json.dumps({"error": error_msg}))

        # Get data key (handles aliases like "ticket" -> "support_ticket")
        data_key = get_entity_data_key(entity_type)

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
        if not isinstance(entity_table, dict) or entity_id not in entity_table:
            return json.loads(json.dumps({"error": f"{entity_type} {entity_id} not found"}))

        entity = entity_table[entity_id]
        old_value = entity.get(field_name)

        # Update the field
        entity[field_name] = field_value

        # Update timestamp if entity has updatedAt field (only orders, tickets, builds have it)
        if "updatedAt" in entity:
            entity["updatedAt"] = get_now_iso_from_data(data)

        return json.loads(json.dumps({
            "success": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "field_name": field_name,
            "old_value": old_value,
            "new_value": field_value,
            "updated_entity": entity,
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "update_entity_field",
                "description": "Generic field updater: update any single field on any entity type. More granular than entity-specific update tools. **IMPORTANT: Use camelCase for field names to match the data schema (e.g., 'assignedEmployeeId' not 'assigned_employee_id'). For employee references, use the employee ID (e.g., 'david-pereboom'), not email or name. If unsure about valid field names, use get_entity_schema first to discover available fields.**",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity to update.",
                            "enum": VALID_ENTITY_TYPES,
                        },
                        "entity_id": {
                            "type": "string",
                            "description": "ID of the entity to update.",
                        },
                        "field_name": {
                            "type": "string",
                            "description": "Name of the field to update in camelCase. Common fields: 'status', 'priority', 'assignedEmployeeId', 'amount', 'quantity'. For employee assignments use 'assignedEmployeeId'.",
                        },
                        "field_value": {
                            "description": "New value for the field. **For assignedEmployeeId, use the employee's ID (e.g., 'david-pereboom'), not their email or name.** Values can be string, number, boolean, object, or array.",
                        },
                    },
                    "required": ["entity_type", "entity_id", "field_name", "field_value"],
                },
            },
        }
