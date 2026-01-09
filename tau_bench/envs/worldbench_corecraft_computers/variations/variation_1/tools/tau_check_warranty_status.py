import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    get_entity_by_id,
    parse_entity_json_fields,
)


# Default current date (September 8, 2025) - must match JavaScript implementation
CURRENT_DATE = datetime(2025, 9, 8, 0, 0, 0, tzinfo=timezone.utc)


class CheckWarrantyStatus(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: Optional[str] = None,
        product_id: Optional[str] = None,
        purchase_date: Optional[str] = None,
    ) -> str:
        if not order_id and not product_id:
            raise ValueError("Either order_id or product_id is required")

        warranty_months = 12
        purchase_dt = None
        current_date = data.get("current_time")

        if order_id:
            # Get order
            order = get_entity_by_id(data, "order", order_id)
            if not order:
                return json.dumps({"is_under_warranty": False})

            # Parse JSON fields
            order = parse_entity_json_fields(order, ["lineItems"])

            # Get purchase date from order
            created_at = order.get("createdAt")
            if isinstance(created_at, str):
                purchase_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00')).astimezone(timezone.utc)
            elif isinstance(created_at, (int, float)):
                purchase_dt = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
            elif isinstance(created_at, datetime):
                purchase_dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
                purchase_dt = purchase_dt.astimezone(timezone.utc)
            else:
                purchase_dt = CURRENT_DATE

            # If product_id is provided, get specific warranty for that product
            if product_id and order.get("lineItems"):
                line_items = order.get("lineItems")
                if isinstance(line_items, list):
                    for item in line_items:
                        if isinstance(item, dict) and item.get("productId") == product_id:
                            # Get product warranty
                            product = get_entity_by_id(data, "product", product_id)
                            if product and product.get("warrantyMonths"):
                                warranty_months = product.get("warrantyMonths")
                            break

        elif product_id:
            # Get product
            product = get_entity_by_id(data, "product", product_id)
            if not product:
                return json.dumps({"is_under_warranty": False})

            warranty_months = product.get("warrantyMonths", 12)

            # Use provided purchase date or default
            if purchase_date:
                parsed_purchase = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
                if parsed_purchase.tzinfo:
                    purchase_dt = parsed_purchase.astimezone(timezone.utc)
                else:
                    purchase_dt = parsed_purchase.replace(tzinfo=timezone.utc)
            else:
                purchase_dt = CURRENT_DATE

        # Use current_date parameter if provided, otherwise use hardcoded CURRENT_DATE
        if current_date:
            parsed_current = datetime.fromisoformat(current_date.replace('Z', '+00:00'))
            if parsed_current.tzinfo:
                current_dt = parsed_current.astimezone(timezone.utc)
            else:
                current_dt = parsed_current.replace(tzinfo=timezone.utc)
        else:
            current_dt = CURRENT_DATE

        # Calculate warranty end date using proper month arithmetic
        year = purchase_dt.year
        month = purchase_dt.month + warranty_months

        # Handle year overflow
        while month > 12:
            year += 1
            month -= 12

        # Try to set to the target year/month with original day and time
        try:
            warranty_end_dt = purchase_dt.replace(year=year, month=month)
        except ValueError:
            # Day doesn't exist in target month (e.g., Jan 31 -> Feb 31)
            if month == 12:
                next_month_first = datetime(
                    year + 1, 1, 1,
                    purchase_dt.hour, purchase_dt.minute, purchase_dt.second, purchase_dt.microsecond,
                    tzinfo=timezone.utc,
                )
            else:
                next_month_first = datetime(
                    year, month + 1, 1,
                    purchase_dt.hour, purchase_dt.minute, purchase_dt.second, purchase_dt.microsecond,
                    tzinfo=timezone.utc,
                )
            warranty_end_dt = next_month_first - timedelta(days=1)

        # Format as YYYY-MM-DD only
        warranty_end_str = warranty_end_dt.date().isoformat()

        # Calculate days remaining
        time_diff_seconds = (warranty_end_dt - current_dt).total_seconds()
        if time_diff_seconds <= 0:
            days_remaining = 0
            is_under_warranty = False
        else:
            days_remaining = max(math.ceil(time_diff_seconds / 86400), 0)
            is_under_warranty = True

        return json.dumps({
            "is_under_warranty": is_under_warranty,
            "warranty_end_date": warranty_end_str,
            "days_remaining": max(days_remaining, 0) if is_under_warranty else 0
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "checkWarrantyStatus",
                "description": "Check whether a product/order is still under warranty based on order details and product warranty terms. Returns is_under_warranty (boolean), warranty_end_date (YYYY-MM-DD string), and days_remaining (number). Either order_id or product_id must be provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID to check warranty status for. If provided, purchase date is derived from the order's creation date."
                        },
                        "product_id": {
                            "type": "string",
                            "description": "The product ID to check warranty for. Can be used alone (with purchase_date) or combined with order_id to check a specific product in an order."
                        },
                        "purchase_date": {
                            "type": "string",
                            "description": "The purchase date (ISO 8601 format with UTC timezone, e.g., \"2025-01-15T00:00:00Z\"). Required when using product_id without order_id."
                        }
                    },
                    "required": [],
                },
            },
        }
