import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import get_entity_data_key, VALID_ENTITY_TYPES, validate_enum_value
except ImportError:
    from utils import get_entity_data_key, VALID_ENTITY_TYPES, validate_enum_value


class AggregateByField(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        group_by_field: str,
        count_field: Optional[str] = None,
    ) -> str:
        """Group entities by a field value and count or sum another field."""
        # Validate entity_type enum
        error_msg = validate_enum_value(entity_type, VALID_ENTITY_TYPES, "entity_type")
        if error_msg:
            return json.loads(json.dumps({"error": error_msg}))

        data_key = get_entity_data_key(entity_type)
        if not data_key:
            return json.loads(json.dumps({"error": f"Unknown entity type: {entity_type}"}))

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict):
            return json.loads(json.dumps({"aggregations": {}, "total": 0}))

        # Group by field value
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for entity in entity_table.values():
            if not isinstance(entity, dict):
                continue

            group_value = str(entity.get(group_by_field, "null"))
            if group_value not in groups:
                groups[group_value] = []
            groups[group_value].append(entity)

        # Calculate aggregations
        aggregations = {}
        for group_value, entities in groups.items():
            count = len(entities)

            agg_result: Dict[str, Any] = {"count": count}

            # If count_field specified, sum or average it
            if count_field:
                values = []
                for entity in entities:
                    val = entity.get(count_field)
                    if val is not None:
                        try:
                            values.append(float(val))
                        except (ValueError, TypeError):
                            pass

                if values:
                    agg_result["sum"] = sum(values)
                    agg_result["average"] = sum(values) / len(values)
                    agg_result["min"] = min(values)
                    agg_result["max"] = max(values)

            aggregations[group_value] = agg_result

        return json.loads(json.dumps({
            "entity_type": entity_type,
            "grouped_by": group_by_field,
            "aggregations": aggregations,
            "total_entities": sum(agg["count"] for agg in aggregations.values()),
            "unique_groups": len(aggregations),
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "aggregate_by_field",
                "description": "Group entities by a field value and count them. Optionally sum/average/min/max another numeric field.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity.",
                            "enum": VALID_ENTITY_TYPES,
                        },
                        "group_by_field": {
                            "type": "string",
                            "description": "Field name to group by (e.g., 'status', 'priority', 'loyaltyTier').",
                        },
                        "count_field": {
                            "type": "string",
                            "description": "Optional numeric field to sum/average (e.g., 'amount', 'total').",
                        },
                    },
                    "required": ["entity_type", "group_by_field"],
                },
            },
        }
