import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool


class GetEntityField(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        entity_id: str,
        fields: Optional[List[str]] = None,
    ) -> str:
        """Get specific field(s) from any entity. Returns just the field values."""
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
            "knowledge_base": "knowledge_base_article",
        }

        data_key = entity_map.get(entity_type.lower())
        if not data_key:
            return json.loads(json.dumps({"error": f"Unknown entity type: {entity_type}"}))

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict) or entity_id not in entity_table:
            return json.loads(json.dumps({"error": f"{entity_type} {entity_id} not found"}))

        entity = entity_table[entity_id]

        # If no fields specified, return all fields
        if not fields:
            return json.loads(json.dumps({
                "entity_id": entity_id,
                "entity_type": entity_type,
                "fields": entity,
            }))

        # Extract specific fields
        field_values = {}
        for field in fields:
            field_values[field] = entity.get(field)

        return json.loads(json.dumps({
            "entity_id": entity_id,
            "entity_type": entity_type,
            "fields": field_values,
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_entity_field",
                "description": "Get specific field(s) from any entity type. Returns just the requested field values. If no fields specified, returns entire entity.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity (customer, order, ticket, payment, shipment, product, etc.).",
                        },
                        "entity_id": {
                            "type": "string",
                            "description": "ID of the entity.",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of field names to retrieve. If omitted, returns all fields.",
                        },
                    },
                    "required": ["entity_type", "entity_id"],
                },
            },
        }
