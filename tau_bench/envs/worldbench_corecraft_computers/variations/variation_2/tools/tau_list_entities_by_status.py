import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class ListEntitiesByStatus(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], entity_type: str) -> str:
        """Get all entities of a type grouped by their status field."""
        entity_map = {
            "order": "order",
            "ticket": "support_ticket",
            "support_ticket": "support_ticket",
            "payment": "payment",
            "shipment": "shipment",
            "refund": "refund",
            "escalation": "escalation",
        }

        data_key = entity_map.get(entity_type.lower())
        if not data_key:
            return json.loads(json.dumps({"error": f"Unknown entity type: {entity_type}"}))

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict):
            return json.loads(json.dumps({"by_status": {}, "total": 0}))

        # Group by status
        by_status: Dict[str, List[Dict[str, Any]]] = {}

        for entity in entity_table.values():
            if not isinstance(entity, dict):
                continue

            status = entity.get("status", "unknown")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(entity)

        # Calculate counts
        status_counts = {status: len(entities) for status, entities in by_status.items()}

        return json.loads(json.dumps({
            "entity_type": entity_type,
            "by_status": by_status,
            "status_counts": status_counts,
            "total": sum(status_counts.values()),
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_entities_by_status",
                "description": "Get all entities of a type (order, ticket, payment, shipment, refund, escalation) grouped by their status field.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity: order, ticket, payment, shipment, refund, or escalation.",
                        },
                    },
                    "required": ["entity_type"],
                },
            },
        }
