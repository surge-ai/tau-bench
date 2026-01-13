import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_iso_datetime,
    get_datetime_field,
    apply_limit,
    validate_enum,
)

PAYMENT_STATUSES = ["pending", "authorized", "captured", "failed", "refunded", "disputed", "voided", "completed"]


class SearchPayments(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        processed_after: Optional[str] = None,
        processed_before: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        validate_enum(status, PAYMENT_STATUSES, "status")

        results: List[Dict[str, Any]] = []

        # Parse date filters, will be None if _before or _after is None
        created_after_dt = parse_iso_datetime(created_after, "created_after")
        created_before_dt = parse_iso_datetime(created_before, "created_before")
        processed_after_dt = parse_iso_datetime(processed_after, "processed_after")
        processed_before_dt = parse_iso_datetime(processed_before, "processed_before")

        for row in iter_entities(data, "payment"):
            # Exact order_id match
            if order_id and row.get("orderId") != order_id:
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
            # If filtering by processedAt, exclude payments that haven't been processed
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
        results.sort(key=lambda p: p.get("id", ""))  # Secondary: id ASC
        results.sort(key=lambda p: p.get("createdAt", "") or "", reverse=True)  # Primary: createdAt DESC

        # Apply limit
        results = apply_limit(results, limit)

        return json.loads(json.dumps(results, default=str))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchPayments",
                "description": "Search for payments with various filters. Returns an array of payment records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Order ID to filter by"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "authorized", "captured", "failed", "refunded", "disputed", "voided", "completed"],
                            "description": "Payment status to filter by"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter payments created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter payments created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        },
                        "processed_after": {
                            "type": "string",
                            "description": "Filter payments processed after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "processed_before": {
                            "type": "string",
                            "description": "Filter payments processed before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
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
