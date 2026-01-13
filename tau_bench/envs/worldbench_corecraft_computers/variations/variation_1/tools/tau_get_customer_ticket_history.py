import json
from typing import Any, Dict, List, Optional, Set

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    get_entity_by_id,
    parse_iso_datetime,
    get_datetime_field,
)


class GetCustomerTicketHistory(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        customer_id: str,
        include_resolved: Optional[bool] = None,
        tkt_created_after: Optional[str] = None,
        tkt_created_before: Optional[str] = None,
        tkt_updated_after: Optional[str] = None,
        tkt_updated_before: Optional[str] = None,
    ) -> str:
        if not customer_id:
            raise ValueError("customer_id is required")

        # Verify customer exists
        customer = get_entity_by_id(data, "customer", customer_id)
        if not customer:
            raise ValueError(f"Customer not found: {customer_id}")

        # Parse date filters
        created_after_dt = parse_iso_datetime(tkt_created_after, "tkt_created_after")
        created_before_dt = parse_iso_datetime(tkt_created_before, "tkt_created_before")
        updated_after_dt = parse_iso_datetime(tkt_updated_after, "tkt_updated_after")
        updated_before_dt = parse_iso_datetime(tkt_updated_before, "tkt_updated_before")

        include_resolved_bool = include_resolved if include_resolved is not None else True

        # Find matching tickets
        tickets: List[Dict[str, Any]] = []
        ticket_ids: Set[str] = set()  # Use set for O(1) lookup

        for row in iter_entities(data, "support_ticket"):
            if row.get("customerId") != customer_id:
                continue
            if not include_resolved_bool:
                if row.get("status") in ("resolved", "closed"):
                    continue
            # Date filtering - createdAt
            created_at = get_datetime_field(row, "createdAt")
            if created_at is not None:
                if created_after_dt and created_at < created_after_dt:
                    continue
                if created_before_dt and created_at >= created_before_dt:
                    continue
            # Date filtering - updatedAt
            updated_at = get_datetime_field(row, "updatedAt")
            if updated_at is not None:
                if updated_after_dt and updated_at < updated_after_dt:
                    continue
                if updated_before_dt and updated_at >= updated_before_dt:
                    continue

            formatted_ticket = {
                "id": row.get("id"),
                "customerId": row.get("customerId"),
                "category": row.get("ticketType"),
                "status": row.get("status"),
                "priority": row.get("priority"),
                "subject": row.get("subject"),
                "createdAt": row.get("createdAt"),
                "updatedAt": row.get("updatedAt"),
            }
            tickets.append(formatted_ticket)
            ticket_ids.add(row.get("id"))

        # Sort by createdAt DESC, then id ASC
        tickets.sort(key=lambda t: t.get("id", ""))  # Secondary: id ASC
        tickets.sort(key=lambda t: t.get("createdAt", "") or "", reverse=True)  # Primary: createdAt DESC

        # Get escalations for these tickets
        escalations: List[Dict[str, Any]] = []
        for e in iter_entities(data, "escalation"):
            if e.get("ticketId") in ticket_ids:
                escalations.append({
                    "id": e.get("id"),
                    "ticketId": e.get("ticketId"),
                    "escalation_type": e.get("escalationType"),
                    "destination": e.get("destination"),
                })

        # Get resolutions for these tickets
        resolutions: List[Dict[str, Any]] = []
        for r in iter_entities(data, "resolution"):
            if r.get("ticketId") in ticket_ids:
                resolutions.append({
                    "id": r.get("id"),
                    "ticketId": r.get("ticketId"),
                    "outcome": r.get("outcome"),
                    "details": r.get("details"),
                })

        return json.dumps({
            "tickets": tickets,
            "escalations": escalations,
            "resolutions": resolutions
        }, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "getCustomerTicketHistory",
                "description": "Get a customer's support ticket history including escalations and resolutions. Returns an object with tickets (array of support tickets), escalations (array of escalation records), and resolutions (array of resolution records).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer ID to retrieve ticket history for"
                        },
                        "include_resolved": {
                            "type": "boolean",
                            "description": "Include resolved/closed tickets. Set to false to exclude them (default: true)"
                        },
                        "tkt_created_after": {
                            "type": "string",
                            "description": "Filter tickets created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "tkt_created_before": {
                            "type": "string",
                            "description": "Filter tickets created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "tkt_updated_after": {
                            "type": "string",
                            "description": "Filter tickets updated after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "tkt_updated_before": {
                            "type": "string",
                            "description": "Filter tickets updated before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        }
                    },
                    "required": ["customer_id"],
                },
            },
        }
