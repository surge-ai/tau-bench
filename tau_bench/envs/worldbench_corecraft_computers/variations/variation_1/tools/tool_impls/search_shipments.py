import json
from typing import Annotated, List, Optional

from models import Shipment
from pydantic import Field
from utils import get_db_conn, validate_date_format, parse_datetime_to_timestamp


def searchShipments(
    order_id: Annotated[Optional[str], Field(description="Order ID to filter by")] = None,
    tracking_number: Annotated[Optional[str], Field(description="Tracking number to filter by")] = None,
    created_after: Annotated[
        Optional[str],
        Field(description="Filter shipments created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")")
    ] = None,
    created_before: Annotated[
        Optional[str],
        Field(description="Filter shipments created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")")
    ] = None,
    limit: Annotated[
        Optional[float],
        Field(description="Maximum number of results (default 50, max 200)"),
    ] = None,
) -> List[Shipment]:
    """Search for shipments"""
    # Validate and normalize date formats
    if created_after:
        created_after = validate_date_format(created_after, "created_after")
    if created_before:
        created_before = validate_date_format(created_before, "created_before")
    
    limit = int(limit) if limit else 50
    limit = min(limit, 200)

    conditions = []
    params = []

    if order_id:
        conditions.append("orderId = ?")
        params.append(order_id)

    if tracking_number:
        conditions.append("trackingNumber = ?")
        params.append(tracking_number)

    if created_after:
        conditions.append("createdAt >= ?")
        params.append(parse_datetime_to_timestamp(created_after))

    if created_before:
        conditions.append("createdAt <= ?")
        params.append(parse_datetime_to_timestamp(created_before))

    params.append(limit)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM Shipment {where_clause} ORDER BY createdAt DESC, id ASC LIMIT ?"

    conn = get_db_conn()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)

            # Parse JSON fields
            if "events" in row_dict and isinstance(row_dict["events"], str):
                try:
                    row_dict["events"] = json.loads(row_dict["events"])
                except (json.JSONDecodeError, TypeError):
                    pass

            results.append(Shipment(**row_dict))

        return results
    finally:
        conn.close()
