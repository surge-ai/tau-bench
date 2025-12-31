import json
from typing import Annotated, List, Optional

from models import Order
from pydantic import Field
from utils import (get_db_conn, parse_datetime_to_timestamp,
                   validate_date_format)


def searchOrders(
    order_id: Annotated[Optional[str], Field(description="Specific order ID to find")] = None,
    customer_id: Annotated[Optional[str], Field(description="Customer ID to filter by")] = None,
    product_id: Annotated[Optional[str], Field(description="Product ID to search within order line items")] = None,
    status: Annotated[
        Optional[str],
        Field(description="Order status to filter by. Valid values: \"pending\", \"paid\", \"fulfilled\", \"cancelled\", \"refunded\", \"partially_refunded\", \"backorder\"")
    ] = None,
    created_after: Annotated[
        Optional[str],
        Field(description="Filter orders created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-14T00:00:00Z\")")
    ] = None,
    created_before: Annotated[
        Optional[str],
        Field(description="Filter orders created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-15T00:00:00Z\")")
    ] = None,
    limit: Annotated[
        Optional[float],
        Field(description="Maximum number of results (default 10, max 10)"),
    ] = None,
) -> List[Order]:
    """Search for orders"""
    # Validate and normalize date formats
    if created_after:
        created_after = validate_date_format(created_after, "created_after")
    if created_before:
        created_before = validate_date_format(created_before, "created_before")

    limit = int(limit) if limit else 10
    limit = min(limit, 10)

    conditions = []
    params = []

    if customer_id:
        conditions.append("customerId = ?")
        params.append(customer_id)

    if status:
        conditions.append("status = ?")
        params.append(status)

    if created_after:
        conditions.append("createdAt >= ?")
        params.append(parse_datetime_to_timestamp(created_after))

    if created_before:
        conditions.append("createdAt <= ?")
        params.append(parse_datetime_to_timestamp(created_before))

    if order_id:
        conditions.append("id = ?")
        params.append(order_id)

    if product_id:
        conditions.append("lineItems LIKE ?")
        params.append(f'%"productId":"{product_id}"%')

    params.append(limit)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    # Use "Order" with quotes because it's a SQL keyword
    sql = f"SELECT * FROM \"Order\" {where_clause} ORDER BY createdAt DESC, id ASC LIMIT ?"

    conn = get_db_conn()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)

            # Parse JSON fields
            for field in ["lineItems", "shipping"]:
                if field in row_dict and isinstance(row_dict[field], str):
                    try:
                        row_dict[field] = json.loads(row_dict[field])
                    except (json.JSONDecodeError, TypeError):
                        pass

            results.append(Order(**row_dict))

        return results
    finally:
        conn.close()
