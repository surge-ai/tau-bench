import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_iso_datetime,
    get_datetime_field,
    apply_limit,
    matches_text_search,
    validate_enum,
)


class SearchEscalations(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        escalation_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        escalation_type: Optional[str] = None,
        destination: Optional[str] = None,
        notes_text: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        resolved_after: Optional[str] = None,
        resolved_before: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        # Validate enum parameters
        validate_enum(escalation_type, ["technical", "policy_exception", "product_specialist", "insufficient_permission"], "escalation_type")
        validate_enum(destination, ["operations", "order_processing", "engineering", "help_desk", "it_systems", "product_management", "finance", "hr", "support"], "destination")

        results: List[Dict[str, Any]] = []

        # Parse date filters, will be None if _before or _after is None
        created_after_dt = parse_iso_datetime(created_after, "created_after")
        created_before_dt = parse_iso_datetime(created_before, "created_before")
        resolved_after_dt = parse_iso_datetime(resolved_after, "resolved_after")
        resolved_before_dt = parse_iso_datetime(resolved_before, "resolved_before")

        for row in iter_entities(data, "escalation"):
            # Exact escalation_id match
            if escalation_id and row.get("id") != escalation_id:
                continue
            # Exact ticket_id match
            if ticket_id and row.get("ticketId") != ticket_id:
                continue
            # Exact escalation_type match
            if escalation_type and row.get("escalationType") != escalation_type:
                continue
            # Exact destination match
            if destination and row.get("destination") != destination:
                continue
            # Partial text search on notes
            if notes_text and not matches_text_search(row, ["notes"], notes_text):
                continue
            # Date filtering - createdAt
            created_at = get_datetime_field(row, "createdAt")
            if created_at is not None:
                if created_after_dt and created_at < created_after_dt:
                    continue
                if created_before_dt and created_at > created_before_dt:
                    continue
            # Date filtering - resolvedAt
            # If filtering by resolvedAt, exclude escalations that haven't been resolved
            resolved_at = get_datetime_field(row, "resolvedAt")
            if resolved_after_dt or resolved_before_dt:
                if resolved_at is None:
                    continue
                if resolved_after_dt and resolved_at < resolved_after_dt:
                    continue
                if resolved_before_dt and resolved_at > resolved_before_dt:
                    continue

            results.append(dict(row))

        # Sort by createdAt DESC, then by id ASC
        results.sort(key=lambda e: e.get("id", ""))  # Secondary: id ASC
        results.sort(key=lambda e: e.get("createdAt", "") or "", reverse=True)  # Primary: createdAt DESC

        # Apply limit
        results = apply_limit(results, limit)

        return json.loads(json.dumps(results, default=str))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchEscalations",
                "description": "Search for escalations with various filters. Returns an array of escalation records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "escalation_id": {
                            "type": "string",
                            "description": "Escalation ID to filter by"
                        },
                        "ticket_id": {
                            "type": "string",
                            "description": "Ticket ID to filter by"
                        },
                        "escalation_type": {
                            "type": "string",
                            "enum": ["technical", "policy_exception", "product_specialist", "insufficient_permission"],
                            "description": "Escalation type to filter by"
                        },
                        "destination": {
                            "type": "string",
                            "enum": ["operations", "order_processing", "engineering", "help_desk", "it_systems", "product_management", "finance", "hr", "support"],
                            "description": "Escalation destination to filter by"
                        },
                        "notes_text": {
                            "type": "string",
                            "description": "Text to search for within escalation notes (case-insensitive partial match)"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter escalations created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter escalations created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        },
                        "resolved_after": {
                            "type": "string",
                            "description": "Filter escalations resolved after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "resolved_before": {
                            "type": "string",
                            "description": "Filter escalations resolved before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
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
