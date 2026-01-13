import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from tau_bench.envs.tool import Tool


class FilterByDateRange(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        date_field: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Filter entities by date range on any date field."""
        entity_map = {
            "customer": "customer",
            "order": "order",
            "ticket": "support_ticket",
            "support_ticket": "support_ticket",
            "payment": "payment",
            "shipment": "shipment",
            "refund": "refund",
            "escalation": "escalation",
            "resolution": "resolution",
        }

        data_key = entity_map.get(entity_type.lower())
        if not data_key:
            return json.loads(json.dumps({"error": f"Unknown entity type: {entity_type}"}))

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict):
            return json.loads(json.dumps({"results": [], "count": 0}))

        # Parse date range
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return json.loads(json.dumps({"error": f"Invalid start_date format: {start_date}"}))

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return json.loads(json.dumps({"error": f"Invalid end_date format: {end_date}"}))

        results = []

        for entity in entity_table.values():
            if not isinstance(entity, dict):
                continue

            date_value = entity.get(date_field)
            if not date_value:
                continue

            try:
                # Parse entity date
                if isinstance(date_value, str):
                    entity_dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                else:
                    continue

                # Check if within range
                if start_dt and entity_dt < start_dt:
                    continue
                if end_dt and entity_dt > end_dt:
                    continue

                results.append(entity)

            except (ValueError, AttributeError):
                # Skip entities with unparseable dates
                continue

        return json.loads(json.dumps({
            "entity_type": entity_type,
            "date_field": date_field,
            "start_date": start_date,
            "end_date": end_date,
            "results": results,
            "count": len(results),
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "filter_by_date_range",
                "description": "Filter entities by date range on any date field (createdAt, updatedAt, resolvedAt, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity (order, ticket, payment, shipment, refund, etc.).",
                        },
                        "date_field": {
                            "type": "string",
                            "description": "Date field to filter on (e.g., 'createdAt', 'updatedAt', 'resolvedAt').",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (ISO 8601 format, e.g., '2024-01-01T00:00:00Z'). Inclusive.",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (ISO 8601 format). Inclusive.",
                        },
                    },
                    "required": ["entity_type", "date_field"],
                },
            },
        }
