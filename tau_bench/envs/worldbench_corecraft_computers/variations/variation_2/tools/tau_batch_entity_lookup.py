import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import get_entity_data_key, VALID_ENTITY_TYPES, validate_enum_value
except ImportError:
    from utils import get_entity_data_key, VALID_ENTITY_TYPES, validate_enum_value


class BatchEntityLookup(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        entity_ids: List[str],
    ) -> str:
        """Look up multiple entities of the same type in one call."""
        # Validate entity_type enum
        error_msg = validate_enum_value(entity_type, VALID_ENTITY_TYPES, "entity_type")
        if error_msg:
            return json.loads(json.dumps({"error": error_msg}))

        data_key = get_entity_data_key(entity_type)
        if not data_key:
            return json.loads(json.dumps({"error": f"Unknown entity type: {entity_type}"}))

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict):
            return json.loads(json.dumps({"found": [], "not_found": entity_ids, "count": 0}))

        found = []
        not_found = []

        for entity_id in entity_ids:
            if entity_id in entity_table:
                found.append(entity_table[entity_id])
            else:
                not_found.append(entity_id)

        return json.loads(json.dumps({
            "entity_type": entity_type,
            "found": found,
            "not_found": not_found,
            "count": len(found),
        }))

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
                            "description": "Type of entity.",
                            "enum": VALID_ENTITY_TYPES,
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
