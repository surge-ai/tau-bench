import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


def _now_iso_from_data(data: Dict[str, Any]) -> str:
    """Get deterministic timestamp from data or use fallback."""
    for k in ("__now", "now", "current_time", "currentTime"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return "1970-01-01T00:00:00Z"


class BulkStatusUpdate(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        entity_ids: List[str],
        status: str,
    ) -> str:
        """Bulk update status for multiple entities (orders, tickets, payments, shipments)."""
        entity_map = {
            "order": "order",
            "ticket": "support_ticket",
            "support_ticket": "support_ticket",
            "payment": "payment",
            "shipment": "shipment",
        }

        data_key = entity_map.get(entity_type.lower())
        if not data_key:
            return json.loads(json.dumps({"error": f"Unknown entity type: {entity_type}"}))

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict):
            return json.loads(json.dumps({"error": f"No {entity_type} data available"}))

        results = {
            "updated": [],
            "not_found": [],
            "errors": [],
        }

        for entity_id in entity_ids:
            if entity_id not in entity_table:
                results["not_found"].append(entity_id)
                continue

            entity = entity_table[entity_id]
            if not isinstance(entity, dict):
                results["errors"].append({"id": entity_id, "error": "Invalid entity format"})
                continue

            # Update status
            old_status = entity.get("status")
            entity["status"] = status
            entity["updatedAt"] = _now_iso_from_data(data)

            # Set special fields based on status
            if entity_type in ["ticket", "support_ticket"]:
                if status in ["resolved", "closed"] and not entity.get("resolvedAt"):
                    entity["resolvedAt"] = _now_iso_from_data(data)

            if entity_type == "payment":
                if status == "completed" and not entity.get("completedAt"):
                    entity["completedAt"] = _now_iso_from_data(data)
                elif status == "failed" and not entity.get("failedAt"):
                    entity["failedAt"] = _now_iso_from_data(data)

            if entity_type == "shipment":
                if status == "delivered" and not entity.get("deliveredAt"):
                    entity["deliveredAt"] = _now_iso_from_data(data)

            results["updated"].append({
                "id": entity_id,
                "old_status": old_status,
                "new_status": status,
            })

        return json.loads(json.dumps({
            "success": len(results["updated"]) > 0,
            "entity_type": entity_type,
            "status": status,
            "results": results,
            "summary": {
                "total": len(entity_ids),
                "updated": len(results["updated"]),
                "not_found": len(results["not_found"]),
                "errors": len(results["errors"]),
            },
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "bulk_status_update",
                "description": "Bulk update status for multiple entities (orders, tickets, payments, shipments) at once.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity: order, ticket, payment, or shipment.",
                        },
                        "entity_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of entity IDs to update.",
                        },
                        "status": {
                            "type": "string",
                            "description": "New status to set for all entities.",
                        },
                    },
                    "required": ["entity_type", "entity_ids", "status"],
                },
            },
        }
