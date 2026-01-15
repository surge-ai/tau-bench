import json
from typing import Any, Dict, List

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


class BulkStatusUpdate(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        entity_ids: List[str],
        status: str,
    ) -> str:
        """Bulk update status for multiple entities (orders, tickets, payments, shipments)."""
        # Validate entity_type enum
        allowed_types = ["order", "ticket", "support_ticket", "payment", "shipment"]
        error_msg = validate_enum_value(entity_type, allowed_types, "entity_type")
        if error_msg:
            return json.loads(json.dumps({"error": error_msg}))

        # Get data key (handles aliases like "ticket" -> "support_ticket")
        data_key = get_entity_data_key(entity_type)

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

            # Update timestamp only for entity types that have updatedAt (orders, tickets)
            if "updatedAt" in entity:
                entity["updatedAt"] = _now_iso_from_data(data)

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
                            "description": "Type of entity to bulk update.",
                            "enum": ["order", "ticket", "support_ticket", "payment", "shipment"],
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
