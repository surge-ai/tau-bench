import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_iso_datetime,
    get_datetime_field,
    matches_text_search,
    apply_limit,
    validate_enum,
)

TICKET_STATUSES = ["new", "open", "pending_customer", "resolved", "closed"]
TICKET_PRIORITIES = ["low", "normal", "high"]
TICKET_TYPES = ["return", "troubleshooting", "recommendation", "order_issue", "shipping", "billing", "other"]


class SearchTickets(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        ticket_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        assigned_employee_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        ticket_type: Optional[str] = None,
        text: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        resolved_after: Optional[str] = None,
        resolved_before: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        validate_enum(status, TICKET_STATUSES, "status")
        validate_enum(priority, TICKET_PRIORITIES, "priority")
        validate_enum(ticket_type, TICKET_TYPES, "ticket_type")

        results: List[Dict[str, Any]] = []

        # Parse date filters
        created_after_dt = parse_iso_datetime(created_after, "created_after")
        created_before_dt = parse_iso_datetime(created_before, "created_before")
        resolved_after_dt = parse_iso_datetime(resolved_after, "resolved_after")
        resolved_before_dt = parse_iso_datetime(resolved_before, "resolved_before")

        for row in iter_entities(data, "support_ticket"):
            # Exact ticket_id match
            if ticket_id and row.get("id") != ticket_id:
                continue
            # Exact customer_id match
            if customer_id and row.get("customerId") != customer_id:
                continue
            # Exact assigned_employee_id match
            if assigned_employee_id and row.get("assignedEmployeeId") != assigned_employee_id:
                continue
            # Exact status match
            if status and row.get("status") != status:
                continue
            # Exact priority match
            if priority and row.get("priority") != priority:
                continue
            # Exact ticket_type match
            if ticket_type and row.get("ticketType") != ticket_type:
                continue
            # Text search in subject and body
            if text and not matches_text_search(row, ["subject", "body"], text):
                continue
            # Date filtering - createdAt
            created_at = get_datetime_field(row, "createdAt")
            if created_at is not None:
                if created_after_dt and created_at < created_after_dt:
                    continue
                if created_before_dt and created_at > created_before_dt:
                    continue
            # Date filtering - resolved (uses updatedAt)
            updated_at = get_datetime_field(row, "updatedAt")
            if updated_at is not None:
                if resolved_after_dt and updated_at < resolved_after_dt:
                    continue
                if resolved_before_dt and updated_at > resolved_before_dt:
                    continue

            results.append(dict(row))

        # Sort by priority (high -> normal -> low), then by createdAt DESC, then by id ASC
        # Using Python's stable sort: sort by least significant key first, then more significant
        priority_order = {"high": 1, "normal": 2, "low": 3}
        results.sort(key=lambda t: t.get("id", ""))  # Tertiary: id ASC
        results.sort(key=lambda t: t.get("createdAt", "") or "", reverse=True)  # Secondary: createdAt DESC
        results.sort(key=lambda t: priority_order.get(t.get("priority", "normal"), 4))  # Primary: priority ASC

        # Apply limit
        results = apply_limit(results, limit)

        return json.dumps(results, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchTickets",
                "description": "Search for support tickets with various filters. Returns an array of support ticket records matching the criteria, sorted by priority (high to low) and then by creation date (newest first).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "Specific ticket ID to find"
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID to filter by"
                        },
                        "assigned_employee_id": {
                            "type": "string",
                            "description": "Employee ID to filter by"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["new", "open", "pending_customer", "resolved", "closed"],
                            "description": "Ticket status to filter by"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "normal", "high"],
                            "description": "Ticket priority to filter by"
                        },
                        "ticket_type": {
                            "type": "string",
                            "enum": ["return", "troubleshooting", "recommendation", "order_issue", "shipping", "billing", "other"],
                            "description": "Ticket type to filter by"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to search in subject and body. Searches for exact matches (case insensitive)."
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter tickets created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter tickets created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        },
                        "resolved_after": {
                            "type": "string",
                            "description": "Filter tickets resolved after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "resolved_before": {
                            "type": "string",
                            "description": "Filter tickets resolved before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
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
