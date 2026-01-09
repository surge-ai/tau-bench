import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_iso_datetime,
    parse_entity_json_fields,
    get_created_at,
    apply_limit,
)


class SearchBuilds(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        name: Optional[str] = None,
        customer_id: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        results: List[Dict[str, Any]] = []

        # Parse date filters
        created_after_dt = parse_iso_datetime(created_after) if created_after else None
        created_before_dt = parse_iso_datetime(created_before) if created_before else None

        for row in iter_entities(data, "build"):
            # Exact customer_id match
            if customer_id and row.get("customerId") != customer_id:
                continue
            # Partial name match (case insensitive)
            if name:
                row_name = row.get("name", "")
                if name.lower() not in row_name.lower():
                    continue
            # Date filtering - createdAt
            created_at = get_created_at(row)
            if created_at is not None:
                if created_after_dt and created_at < created_after_dt:
                    continue
                if created_before_dt and created_at > created_before_dt:
                    continue

            # Parse JSON fields
            result_row = parse_entity_json_fields(row, ["componentIds"])
            results.append(result_row)

        # Sort by name ASC, then by id ASC
        results.sort(key=lambda b: (b.get("name", ""), b.get("id", "")))

        # Apply limit
        results = apply_limit(results, limit)

        return json.dumps(results, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchBuilds",
                "description": "Search for PC builds with various filters. Returns an array of build records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Build name to search for"
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID to filter by"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter builds created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter builds created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default 50, max 200)"
                        }
                    },
                    "required": [],
                },
            },
        }
