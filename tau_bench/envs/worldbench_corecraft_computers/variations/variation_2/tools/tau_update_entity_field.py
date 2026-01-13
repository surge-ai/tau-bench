import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


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
        entity_map = {
            "customer": "customer",
            "order": "order",
            "ticket": "support_ticket",
            "support_ticket": "support_ticket",
            "payment": "payment",
            "shipment": "shipment",
            "product": "product",
            "build": "build",
            "employee": "employee",
            "refund": "refund",
            "escalation": "escalation",
            "resolution": "resolution",
        }

        data_key = entity_map.get(entity_type.lower())
        if not data_key:
            return json.loads(json.dumps({"error": f"Unknown entity type: {entity_type}"}))

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict) or entity_id not in entity_table:
            return json.loads(json.dumps({"error": f"{entity_type} {entity_id} not found"}))

        entity = entity_table[entity_id]
        old_value = entity.get(field_name)

        # Update the field
        entity[field_name] = field_value

        # Update timestamp if entity has updatedAt field
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
                "description": "Generic field updater: update any single field on any entity type. More granular than entity-specific update tools.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity (customer, order, ticket, payment, product, etc.).",
                        },
                        "entity_id": {
                            "type": "string",
                            "description": "ID of the entity to update.",
                        },
                        "field_name": {
                            "type": "string",
                            "description": "Name of the field to update (e.g., 'status', 'priority', 'amount').",
                        },
                        "field_value": {
                            "description": "New value for the field (string, number, boolean, object, or array).",
                        },
                    },
                    "required": ["entity_type", "entity_id", "field_name", "field_value"],
                },
            },
        }
