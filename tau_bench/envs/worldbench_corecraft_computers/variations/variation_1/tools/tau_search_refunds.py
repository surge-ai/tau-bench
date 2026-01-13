import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_iso_datetime,
    get_datetime_field,
    apply_limit,
)


class SearchRefunds(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        refund_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        reason: Optional[str] = None,
        status: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        processed_after: Optional[str] = None,
        processed_before: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        results: List[Dict[str, Any]] = []

        # Parse date filters, will be None if _before or _after is None
        created_after_dt = parse_iso_datetime(created_after, "created_after")
        created_before_dt = parse_iso_datetime(created_before, "created_before")
        processed_after_dt = parse_iso_datetime(processed_after, "processed_after")
        processed_before_dt = parse_iso_datetime(processed_before, "processed_before")

        for row in iter_entities(data, "refund"):
            # Exact refund_id match
            if refund_id and row.get("id") != refund_id:
                continue
            # Exact payment_id match
            if payment_id and row.get("paymentId") != payment_id:
                continue
            # Exact ticket_id match
            if ticket_id and row.get("ticketId") != ticket_id:
                continue
            # Exact reason match
            if reason and row.get("reason") != reason:
                continue
            # Exact status match
            if status and row.get("status") != status:
                continue
            # Date filtering - createdAt
            created_at = get_datetime_field(row, "createdAt")
            if created_at is not None:
                if created_after_dt and created_at < created_after_dt:
                    continue
                if created_before_dt and created_at > created_before_dt:
                    continue
            # Date filtering - processedAt
            # If filtering by processedAt, exclude refunds that haven't been processed
            processed_at = get_datetime_field(row, "processedAt")
            if processed_after_dt or processed_before_dt:
                if processed_at is None:
                    continue
                if processed_after_dt and processed_at < processed_after_dt:
                    continue
                if processed_before_dt and processed_at > processed_before_dt:
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
                "name": "searchRefunds",
                "description": "Search for refunds with various filters. Returns an array of refund records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "refund_id": {
                            "type": "string",
                            "description": "Refund ID to filter by"
                        },
                        "payment_id": {
                            "type": "string",
                            "description": "Payment ID to filter by"
                        },
                        "ticket_id": {
                            "type": "string",
                            "description": "Ticket ID to filter by"
                        },
                        "reason": {
                            "type": "string",
                            "enum": ["customer_remorse", "defective", "incompatible"],
                            "description": "Refund reason to filter by"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "approved", "processed", "rejected"],
                            "description": "Refund status to filter by"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter refunds created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter refunds created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        },
                        "processed_after": {
                            "type": "string",
                            "description": "Filter refunds processed after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "processed_before": {
                            "type": "string",
                            "description": "Filter refunds processed before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
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
