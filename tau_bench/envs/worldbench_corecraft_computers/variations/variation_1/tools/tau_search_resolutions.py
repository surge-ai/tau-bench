import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_iso_datetime,
    get_datetime_field,
    apply_limit,
    matches_text_search,
)


class SearchResolutions(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        resolution_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        outcome: Optional[str] = None,
        resolved_by_id: Optional[str] = None,
        linked_refund_id: Optional[str] = None,
        details_text: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        results: List[Dict[str, Any]] = []

        # Parse date filters, will be None if _before or _after is None
        created_after_dt = parse_iso_datetime(created_after, "created_after")
        created_before_dt = parse_iso_datetime(created_before, "created_before")

        for row in iter_entities(data, "resolution"):
            # Exact resolution_id match
            if resolution_id and row.get("id") != resolution_id:
                continue
            # Exact ticket_id match
            if ticket_id and row.get("ticketId") != ticket_id:
                continue
            # Exact outcome match
            if outcome and row.get("outcome") != outcome:
                continue
            # Exact resolved_by_id match
            if resolved_by_id and row.get("resolvedById") != resolved_by_id:
                continue
            # Exact linked_refund_id match
            if linked_refund_id and row.get("linkedRefundId") != linked_refund_id:
                continue
            # Partial text search on details
            if details_text and not matches_text_search(row, ["details"], details_text):
                continue
            # Date filtering - createdAt
            created_at = get_datetime_field(row, "createdAt")
            if created_at is not None:
                if created_after_dt and created_at < created_after_dt:
                    continue
                if created_before_dt and created_at > created_before_dt:
                    continue

            results.append(dict(row))

        # Sort by createdAt DESC, then by id ASC
        results.sort(key=lambda r: r.get("id", ""))  # Secondary: id ASC
        results.sort(key=lambda r: r.get("createdAt", "") or "", reverse=True)  # Primary: createdAt DESC

        # Apply limit
        results = apply_limit(results, limit)

        return json.dumps(results, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchResolutions",
                "description": "Search for ticket resolutions with various filters. Returns an array of resolution records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resolution_id": {
                            "type": "string",
                            "description": "Resolution ID to filter by"
                        },
                        "ticket_id": {
                            "type": "string",
                            "description": "Ticket ID to filter by"
                        },
                        "outcome": {
                            "type": "string",
                            "enum": ["recommendation_provided", "order_updated", "refund_issued", "troubleshooting_steps"],
                            "description": "Resolution outcome to filter by"
                        },
                        "resolved_by_id": {
                            "type": "string",
                            "description": "Employee ID who resolved the ticket"
                        },
                        "linked_refund_id": {
                            "type": "string",
                            "description": "Linked refund ID to filter by"
                        },
                        "details_text": {
                            "type": "string",
                            "description": "Text to search for within resolution details (case-insensitive partial match)"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter resolutions created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter resolutions created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
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
