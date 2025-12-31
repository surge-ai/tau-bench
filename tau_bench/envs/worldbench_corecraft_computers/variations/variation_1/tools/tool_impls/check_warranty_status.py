import json
import math
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Dict, Optional

from pydantic import Field
from .utils import get_db_conn


# Default current date (September 8, 2025) - must match JavaScript implementation
CURRENT_DATE = datetime(2025, 9, 8, 0, 0, 0, tzinfo=timezone.utc)


def checkWarrantyStatus(
    order_id: Annotated[Optional[str], Field(description="The order_id parameter")] = None,
    product_id: Annotated[Optional[str], Field(description="The product_id parameter")] = None,
    purchase_date: Annotated[Optional[str], Field(description="The purchase_date parameter")] = None,
    current_date: Annotated[Optional[str], Field(description="The current_date parameter")] = None,
) -> Dict[str, Any]:
    """Check warranty status"""
    if not order_id and not product_id:
        raise ValueError("Either order_id or product_id is required")

    warranty_months = 12
    purchase_dt = None

    conn = get_db_conn()

    try:
        cursor = conn.cursor()

        if order_id:
            # Get order
            cursor.execute('SELECT * FROM "Order" WHERE id = ?', [order_id])
            order_row = cursor.fetchone()

            if not order_row:
                return {"is_under_warranty": False}

            order = dict(order_row)

            # Parse JSON fields
            if "lineItems" in order and isinstance(order["lineItems"], str):
                try:
                    order["lineItems"] = json.loads(order["lineItems"])
                except (json.JSONDecodeError, TypeError):
                    pass

            # Get purchase date from order
            created_at = order.get("createdAt")
            if isinstance(created_at, str):
                purchase_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00')).astimezone(timezone.utc)
            elif isinstance(created_at, (int, float)):
                # Handle Unix timestamp (in milliseconds)
                purchase_dt = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
            elif isinstance(created_at, datetime):
                purchase_dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
                purchase_dt = purchase_dt.astimezone(timezone.utc)
            else:
                # Default to current date if we can't parse
                purchase_dt = CURRENT_DATE

            # If product_id is provided, get specific warranty for that product
            if product_id and order.get("lineItems"):
                line_items = order["lineItems"]
                if isinstance(line_items, list):
                    for item in line_items:
                        if isinstance(item, dict) and item.get("productId") == product_id:
                            # Get product warranty
                            cursor.execute("SELECT warrantyMonths FROM Product WHERE id = ?", [product_id])
                            product_row = cursor.fetchone()
                            if product_row and product_row["warrantyMonths"]:
                                warranty_months = product_row["warrantyMonths"]
                            break

        elif product_id:
            # Get product
            cursor.execute("SELECT * FROM Product WHERE id = ?", [product_id])
            product_row = cursor.fetchone()

            if not product_row:
                return {"is_under_warranty": False}

            product = dict(product_row)
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
        # (match JavaScript's setMonth behavior, preserving time component)
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
            # Use the last day of the target month
            if month == 12:
                next_month_first = datetime(
                    year + 1,
                    1,
                    1,
                    purchase_dt.hour,
                    purchase_dt.minute,
                    purchase_dt.second,
                    purchase_dt.microsecond,
                    tzinfo=timezone.utc,
                )
            else:
                next_month_first = datetime(
                    year,
                    month + 1,
                    1,
                    purchase_dt.hour,
                    purchase_dt.minute,
                    purchase_dt.second,
                    purchase_dt.microsecond,
                    tzinfo=timezone.utc,
                )
            warranty_end_dt = next_month_first - timedelta(days=1)

        # Format as YYYY-MM-DD only (match JavaScript format)
        warranty_end_date = warranty_end_dt.date()
        warranty_end_str = warranty_end_date.isoformat()

        # Calculate days remaining using timezone-aware datetime math (ceiling, JS-style)
        time_diff_seconds = (warranty_end_dt - current_dt).total_seconds()
        if time_diff_seconds <= 0:
            days_remaining = 0
            is_under_warranty = False
        else:
            days_remaining = max(math.ceil(time_diff_seconds / 86400), 0)
            is_under_warranty = True

        return {
            "is_under_warranty": is_under_warranty,
            "warranty_end_date": warranty_end_str,
            "days_remaining": max(days_remaining, 0) if is_under_warranty else 0
        }
    finally:
        conn.close()
