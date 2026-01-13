import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_iso_datetime,
    parse_entity_json_fields,
    get_datetime_field,
    matches_json_text_search,
    apply_limit,
    validate_enum,
)

LOYALTY_TIERS = ["none", "silver", "gold", "platinum"]


class SearchCustomers(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        customer_id: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        loyalty_tier: Optional[str] = None,
        address_text: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: Optional[float] = None,
    ) -> str:
        validate_enum(loyalty_tier, LOYALTY_TIERS, "loyalty_tier")

        results: List[Dict[str, Any]] = []

        # Parse date filters
        created_after_dt = parse_iso_datetime(created_after, "created_after")
        created_before_dt = parse_iso_datetime(created_before, "created_before")

        for row in iter_entities(data, "customer"):
            # Exact customer_id match
            if customer_id and row.get("id") != customer_id:
                continue
            # Exact email match
            if email and row.get("email") != email:
                continue
            # Exact phone match
            if phone and row.get("phone") != phone:
                continue
            # Exact loyalty tier match
            if loyalty_tier and row.get("loyaltyTier") != loyalty_tier:
                continue
            # Partial name match (case insensitive)
            if name:
                row_name = row.get("name", "")
                if name.lower() not in row_name.lower():
                    continue
            # Address text search
            if address_text and not matches_json_text_search(row, "addresses", address_text):
                continue
            # Date filtering
            created_at = get_datetime_field(row, "createdAt")
            if created_at is not None:
                if created_after_dt and created_at < created_after_dt:
                    continue
                if created_before_dt and created_at > created_before_dt:
                    continue

            # Parse JSON fields
            result_row = parse_entity_json_fields(row, ["addresses"])
            results.append(result_row)

        # Sort by name ASC, then id ASC
        results.sort(key=lambda c: (c.get("name", ""), c.get("id", "")))

        # Apply limit
        results = apply_limit(results, limit)

        return json.dumps(results, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchCustomers",
                "description": "Search for customers with various filters. Returns an array of customer records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Exact customer ID match"
                        },
                        "name": {
                            "type": "string",
                            "description": "Partial name search (case insensitive)"
                        },
                        "email": {
                            "type": "string",
                            "description": "Exact email address match"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Exact phone number match"
                        },
                        "loyalty_tier": {
                            "type": "string",
                            "enum": ["none", "silver", "gold", "platinum"],
                            "description": "Customer loyalty tier to filter by"
                        },
                        "address_text": {
                            "type": "string",
                            "description": "Text search across all address fields (city, region, postal code, street address, etc.)"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter customers created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter customers created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
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
