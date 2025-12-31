from typing import Annotated, List, Optional

from models import Payment
from pydantic import Field
from utils import get_db_conn, validate_date_format, parse_datetime_to_timestamp


def searchPayments(
    order_id: Annotated[Optional[str], Field(description="Order ID to filter by")] = None,
    status: Annotated[
        Optional[str],
        Field(description="Payment status to filter by. Valid values: \"pending\", \"authorized\", \"captured\", \"failed\", \"refunded\", \"disputed\", \"voided\"")
    ] = None,
    created_after: Annotated[
        Optional[str],
        Field(description="Filter payments created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")")
    ] = None,
    created_before: Annotated[
        Optional[str],
        Field(description="Filter payments created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")")
    ] = None,
    processed_after: Annotated[
        Optional[str],
        Field(description="Filter payments processed after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")")
    ] = None,
    processed_before: Annotated[
        Optional[str],
        Field(description="Filter payments processed before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")")
    ] = None,
    limit: Annotated[
        Optional[float],
        Field(description="Maximum number of results (default 50, max 200)"),
    ] = None,
) -> List[Payment]:
    """Search for payments"""
    # Validate date formats
    if created_after:
        created_after = validate_date_format(created_after, "created_after")
    if created_before:
        created_before = validate_date_format(created_before, "created_before")
    if processed_after:
        processed_after = validate_date_format(processed_after, "processed_after")
    if processed_before:
        processed_before = validate_date_format(processed_before, "processed_before")
    
    limit = int(limit) if limit else 50
    limit = min(limit, 200)

    conditions = []
    params = []

    if order_id:
        conditions.append("orderId = ?")
        params.append(order_id)

    if status:
        conditions.append("status = ?")
        params.append(status)

    if created_after:
        conditions.append("createdAt >= ?")
        params.append(parse_datetime_to_timestamp(created_after))

    if created_before:
        conditions.append("createdAt <= ?")
        params.append(parse_datetime_to_timestamp(created_before))

    if processed_after:
        conditions.append("processedAt >= ?")
        params.append(parse_datetime_to_timestamp(processed_after))

    if processed_before:
        conditions.append("processedAt <= ?")
        params.append(parse_datetime_to_timestamp(processed_before))

    params.append(limit)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM Payment {where_clause} ORDER BY createdAt DESC, id ASC LIMIT ?"

    conn = get_db_conn()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)
            results.append(Payment(**row_dict))

        return results
    finally:
        conn.close()
