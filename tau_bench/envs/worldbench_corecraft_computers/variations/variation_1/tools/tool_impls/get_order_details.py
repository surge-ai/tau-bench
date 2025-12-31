import json
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field
from .utils import get_db_conn, validate_date_format, parse_datetime_to_timestamp


def getOrderDetails(
    order_id: Annotated[str, Field(description="The order_id parameter")],
    created_before: Annotated[
        Optional[str],
        Field(
            description="Filter order details to objects created before this date, inclusive (ISO 8601 format with UTC timezone, e.g., '2025-09-01T00:00:00Z')"
        ),
    ] = None,
) -> Dict[str, Any]:
    """Get order details with related payment, shipment, and tickets"""
    if not order_id:
        raise ValueError("order_id is required")
    
    # Validate created_before format if provided
    if created_before:
        created_before = validate_date_format(created_before, "created_before")
        created_before_timestamp = parse_datetime_to_timestamp(created_before)
    else:
        # Use a far future timestamp if not provided
        created_before_timestamp = 9999999999999

    conn = get_db_conn()

    try:
        cursor = conn.cursor()

        # Get order
        cursor.execute('SELECT * FROM "Order" WHERE id = ?', [order_id])
        order_row = cursor.fetchone()

        if not order_row:
            return {
                "order": None,
                "payment": None,
                "shipment": None,
                "customer": None,
                "tickets": []
            }

        order = dict(order_row)

        # Parse JSON fields in order
        for field in ["lineItems", "shipping"]:
            if field in order and isinstance(order[field], str):
                try:
                    order[field] = json.loads(order[field])
                except (json.JSONDecodeError, TypeError):
                    pass

        # Format order to match JavaScript output (simplified, snake_case)
        # Handle createdAt/updatedAt - can be ISO string or timestamp in ms
        def format_datetime(dt_value):
            if isinstance(dt_value, str):
                # Already ISO format, return as-is (or normalize)
                try:
                    # Parse and reformat to ensure consistent format
                    dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                except (ValueError, AttributeError):
                    return dt_value
            elif isinstance(dt_value, (int, float)):
                # Timestamp in milliseconds
                return datetime.fromtimestamp(dt_value / 1000, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            else:
                return str(dt_value)
        
        formatted_order = {
            "id": order["id"],
            "customer_id": order["customerId"],
            "line_items": order["lineItems"],
            "status": order["status"],
            "created_at": format_datetime(order.get("createdAt", "")),
            "updated_at": format_datetime(order.get("updatedAt", "")),
        }

        # Get customer (only return simplified fields)
        customer = None
        if order.get("customerId"):
            cursor.execute('SELECT name, email, loyaltyTier FROM Customer WHERE id = ?', [order["customerId"]])
            customer_row = cursor.fetchone()
            if customer_row:
                customer = {
                    "name": customer_row["name"],
                    "email": customer_row["email"],
                    "loyalty_tier": customer_row["loyaltyTier"]
                }

        # Get payment (most recent, filtered by created_before)
        payment = None
        cursor.execute(
            'SELECT id, amount, method, status FROM Payment WHERE orderId = ? AND createdAt <= ? ORDER BY createdAt DESC, id ASC LIMIT 1',
            [order_id, created_before_timestamp]
        )
        payment_row = cursor.fetchone()
        if payment_row:
            payment = {
                "id": payment_row["id"],
                "amount": payment_row["amount"],
                "method": payment_row["method"],
                "status": payment_row["status"]
            }

        # Get shipment (most recent, filtered by created_before)
        shipment = None
        cursor.execute(
            'SELECT id, trackingNumber, carrier, status FROM Shipment WHERE orderId = ? AND createdAt <= ? ORDER BY createdAt DESC, id ASC LIMIT 1',
            [order_id, created_before_timestamp]
        )
        shipment_row = cursor.fetchone()
        if shipment_row:
            shipment = {
                "id": shipment_row["id"],
                "tracking_number": shipment_row["trackingNumber"],
                "carrier": shipment_row["carrier"],
                "status": shipment_row["status"]
            }

        # Get tickets (filtered by created_before)
        cursor.execute(
            'SELECT id, subject, status FROM SupportTicket WHERE orderId = ? AND createdAt <= ? ORDER BY createdAt DESC, id ASC',
            [order_id, created_before_timestamp]
        )
        ticket_rows = cursor.fetchall()

        tickets = []
        for ticket_row in ticket_rows:
            tickets.append({
                "id": ticket_row["id"],
                "subject": ticket_row["subject"],
                "status": ticket_row["status"]
            })

        return {
            "order": formatted_order,
            "payment": payment,
            "shipment": shipment,
            "customer": customer,
            "tickets": tickets
        }
    finally:
        conn.close()
