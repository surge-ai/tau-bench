import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class BatchEntityLookup(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        entity_ids: List[str],
    ) -> str:
        """Look up multiple entities of the same type in one call."""
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
            return json.dumps({"error": f"Unknown entity type: {entity_type}"})

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict):
            return json.dumps({"found": [], "not_found": entity_ids, "count": 0})

        found = []
        not_found = []

        for entity_id in entity_ids:
            if entity_id in entity_table:
                found.append(entity_table[entity_id])
            else:
                not_found.append(entity_id)

        return json.dumps({
            "entity_type": entity_type,
            "found": found,
            "not_found": not_found,
            "count": len(found),
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "batch_entity_lookup",
                "description": "Look up multiple entities of the same type in one call. More efficient than individual lookups.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity (customer, order, ticket, payment, shipment, product, etc.).",
                        },
                        "entity_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of entity IDs to look up.",
                        },
                    },
                    "required": ["entity_type", "entity_ids"],
                },
            },
        }
