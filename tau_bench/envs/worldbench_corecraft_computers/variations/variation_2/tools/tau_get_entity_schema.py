import json
from typing import Any, Dict, Set

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import get_entity_data_key, get_entity_table, format_invalid_entity_type_error
except ImportError:
    from utils import get_entity_data_key, get_entity_table, format_invalid_entity_type_error


class GetEntitySchema(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
    ) -> str:
        """Get the set of all field names that exist across entities of a given type."""
        data_key = get_entity_data_key(entity_type)
        if not data_key:
            return json.dumps(format_invalid_entity_type_error(entity_type))

        entity_table = get_entity_table(data, entity_type)
        if entity_table is None:
            return json.dumps({
                "entity_type": entity_type,
                "fields": [],
                "sample_count": 0,
                "message": f"No {entity_type} data available",
            })

        # Collect all unique field names across all entities
        all_fields: Set[str] = set()
        sample_entity = None

        for entity in entity_table.values():
            if isinstance(entity, dict):
                all_fields.update(entity.keys())
                if sample_entity is None:
                    sample_entity = entity

        # Sort fields for consistent output
        sorted_fields = sorted(all_fields)

        # Categorize fields
        system_fields = [f for f in sorted_fields if f in ["id", "type"]]
        timestamp_fields = [f for f in sorted_fields if f.endswith("At")]
        reference_fields = [f for f in sorted_fields if f.endswith("Id") and f not in ["id"]]
        data_fields = [f for f in sorted_fields if f not in system_fields + timestamp_fields + reference_fields]

        # Get field types from sample entity
        field_types = {}
        if sample_entity:
            for field in sorted_fields:
                value = sample_entity.get(field)
                if value is None:
                    field_types[field] = "null"
                elif isinstance(value, bool):
                    field_types[field] = "boolean"
                elif isinstance(value, int):
                    field_types[field] = "integer"
                elif isinstance(value, float):
                    field_types[field] = "number"
                elif isinstance(value, str):
                    field_types[field] = "string"
                elif isinstance(value, list):
                    field_types[field] = "array"
                elif isinstance(value, dict):
                    field_types[field] = "object"
                else:
                    field_types[field] = "unknown"

        result = {
            "entity_type": entity_type,
            "data_key": data_key,
            "total_entities": len(entity_table),
            "fields": {
                "all": sorted_fields,
                "system": system_fields,
                "timestamps": timestamp_fields,
                "references": reference_fields,
                "data": data_fields,
            },
            "field_types": field_types,
            "field_count": len(sorted_fields),
        }

        return json.dumps(result)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_entity_schema",
                "description": "Get the schema (all field names and types) for a given entity type by examining existing entities. Returns all fields that exist across entities of that type, categorized as system fields (id, type), timestamps (*At), references (*Id), and data fields. **Use this tool before update_entity_field to discover valid field names.** Field names are in camelCase format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity to inspect: customer, order, ticket, payment, shipment, product, build, employee, refund, escalation, resolution, knowledge_base_article, slack_channel, slack_message.",
                        },
                    },
                    "required": ["entity_type"],
                },
            },
        }
