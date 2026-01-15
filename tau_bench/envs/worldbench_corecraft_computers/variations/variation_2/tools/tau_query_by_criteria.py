import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import get_entity_data_key, VALID_ENTITY_TYPES, validate_enum_value
except ImportError:
    from utils import get_entity_data_key, VALID_ENTITY_TYPES, validate_enum_value


class QueryByCriteria(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> str:
        """Flexible query tool that searches any entity type with arbitrary filters."""
        filters = filters or {}
        results: List[Dict[str, Any]] = []

        # Validate entity_type enum
        error_msg = validate_enum_value(entity_type, VALID_ENTITY_TYPES, "entity_type")
        if error_msg:
            return json.loads(json.dumps({"error": error_msg}))

        data_key = get_entity_data_key(entity_type)
        if not data_key:
            return json.loads(json.dumps({"error": f"Unknown entity type: {entity_type}"}))

        entity_table = data.get(data_key, {})
        if not isinstance(entity_table, dict):
            return json.loads(json.dumps({"results": []}))

        # Iterate through entities and apply filters
        for entity in entity_table.values():
            if not isinstance(entity, dict):
                continue

            # Check all filter criteria
            matches = True
            for key, value in filters.items():
                entity_value = entity.get(key)

                # Handle different filter types
                if isinstance(value, dict):
                    # Range queries: {"$gte": 100, "$lte": 500}
                    if "$gte" in value and entity_value is not None:
                        if not (entity_value >= value["$gte"]):
                            matches = False
                            break
                    if "$lte" in value and entity_value is not None:
                        if not (entity_value <= value["$lte"]):
                            matches = False
                            break
                    if "$gt" in value and entity_value is not None:
                        if not (entity_value > value["$gt"]):
                            matches = False
                            break
                    if "$lt" in value and entity_value is not None:
                        if not (entity_value < value["$lt"]):
                            matches = False
                            break
                    if "$ne" in value:
                        if entity_value == value["$ne"]:
                            matches = False
                            break
                    if "$in" in value and isinstance(value["$in"], list):
                        if entity_value not in value["$in"]:
                            matches = False
                            break
                    if "$contains" in value and isinstance(entity_value, str):
                        if value["$contains"].lower() not in entity_value.lower():
                            matches = False
                            break
                elif isinstance(value, list):
                    # List means "in" operator
                    if entity_value not in value:
                        matches = False
                        break
                else:
                    # Exact match
                    if entity_value != value:
                        matches = False
                        break

            if matches:
                results.append(entity)
                if limit and len(results) >= limit:
                    break

        return json.loads(json.dumps({"results": results, "count": len(results)}))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "query_by_criteria",
                "description": "Flexible query tool to search any entity type with complex filters. Supports exact match, ranges ($gte, $lte, $gt, $lt), inequality ($ne), inclusion ($in), and text search ($contains).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity.",
                            "enum": VALID_ENTITY_TYPES,
                        },
                        "filters": {
                            "type": "object",
                            "description": "Filter criteria as key-value pairs. Supports exact match, ranges (e.g. {'price': {'$gte': 100, '$lte': 500}}), lists for 'in' operator, and special operators like $contains for text search.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return.",
                        },
                    },
                    "required": ["entity_type"],
                },
            },
        }
