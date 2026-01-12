import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_iso_datetime,
    parse_entity_json_fields,
    get_datetime_field,
    apply_limit,
)


class SearchShipments(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: Optional[str] = None,
        tracking_number: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        results: List[Dict[str, Any]] = []

        # Parse date filters
        created_after_dt = parse_iso_datetime(created_after, "created_after")
        created_before_dt = parse_iso_datetime(created_before, "created_before")

        for row in iter_entities(data, "shipment"):
            # Exact order_id match
            if order_id and row.get("orderId") != order_id:
                continue
            # Exact tracking_number match
            if tracking_number and row.get("trackingNumber") != tracking_number:
                continue
            # Date filtering - createdAt
            created_at = get_datetime_field(row, "createdAt")
            if created_at is not None:
                if created_after_dt and created_at < created_after_dt:
                    continue
                if created_before_dt and created_at > created_before_dt:
                    continue

            # Parse JSON fields
            result_row = parse_entity_json_fields(row, ["events"])
            results.append(result_row)

        # Sort by createdAt DESC, then by id ASC
        results.sort(key=lambda s: s.get("id", ""))  # Secondary: id ASC
        results.sort(key=lambda s: s.get("createdAt", "") or "", reverse=True)  # Primary: createdAt DESC

        # Apply limit
        results = apply_limit(results, limit)

        return json.dumps(results, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchShipments",
                "description": "Search for shipments with various filters. Returns an array of shipment records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Order ID to filter by"
                        },
                        "tracking_number": {
                            "type": "string",
                            "description": "Tracking number to filter by"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter shipments created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter shipments created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default 50, max 200)"
                        }
                    },
                    "required": []
                }
            }
        }
