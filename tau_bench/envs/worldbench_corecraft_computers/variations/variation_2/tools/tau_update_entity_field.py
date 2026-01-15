import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import get_entity_data_key, VALID_ENTITY_TYPES, validate_enum_value
except ImportError:
    from utils import get_entity_data_key, VALID_ENTITY_TYPES, validate_enum_value


def _now_iso_from_data(data: Dict[str, Any]) -> str:
    """Get deterministic timestamp from data or use fallback."""
    for k in ("__now", "now", "current_time", "currentTime"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return "1970-01-01T00:00:00Z"


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

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict) or entity_id not in entity_table:
            return json.loads(json.dumps({"error": f"{entity_type} {entity_id} not found"}))

        entity = entity_table[entity_id]
        old_value = entity.get(field_name)

        # Check if field exists in this entity (helpful warning)
        if field_name not in entity and old_value is None:
            # Collect existing fields for helpful error message
            existing_fields = sorted(entity.keys())
            return json.loads(json.dumps({
                "warning": f"Field '{field_name}' does not exist on this {entity_type}. Creating new field.",
                "suggestion": f"Use get_entity_schema tool with entity_type='{entity_type}' to see valid fields.",
                "existing_fields": existing_fields,
                "field_name": field_name,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "will_create_new_field": True,
            }))

        # Update the field
        entity[field_name] = field_value

        # Update timestamp if entity has updatedAt field (only orders, tickets, builds have it)
        if "updatedAt" in entity:
            entity["updatedAt"] = _now_iso_from_data(data)

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
