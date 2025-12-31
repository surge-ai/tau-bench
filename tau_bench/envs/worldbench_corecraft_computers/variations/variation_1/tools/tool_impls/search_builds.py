import json
from typing import Annotated, List, Optional

from ..models import Build
from pydantic import Field
from .utils import get_db_conn, validate_date_format, parse_datetime_to_timestamp


def searchBuilds(
    name: Annotated[Optional[str], Field(description="Build name to search for")] = None,
    customer_id: Annotated[Optional[str], Field(description="Customer ID to filter by")] = None,
    created_after: Annotated[
        Optional[str],
        Field(description="Filter builds created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")")
    ] = None,
    created_before: Annotated[
        Optional[str],
        Field(description="Filter builds created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")")
    ] = None,
    limit: Annotated[
        Optional[float],
        Field(description="Maximum number of results (default 50, max 200)"),
    ] = None,
) -> List[Build]:
    """Search for builds"""
    # Validate date formats
    if created_after:
        created_after = validate_date_format(created_after, "created_after")
    if created_before:
        created_before = validate_date_format(created_before, "created_before")
    
    limit = int(limit) if limit else 50
    limit = min(limit, 200)

    conditions = []
    params = []

    if name:
        conditions.append("name LIKE ?")
        params.append(f"%{name}%")

    if customer_id:
        conditions.append("customerId = ?")
        params.append(customer_id)

    if created_after:
        conditions.append("createdAt >= ?")
        params.append(parse_datetime_to_timestamp(created_after))

    if created_before:
        conditions.append("createdAt <= ?")
        params.append(parse_datetime_to_timestamp(created_before))

    params.append(limit)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM Build {where_clause} ORDER BY name ASC, id ASC LIMIT ?"

    conn = get_db_conn()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)

            # Parse JSON fields
            if "componentIds" in row_dict and isinstance(row_dict["componentIds"], str):
                try:
                    row_dict["componentIds"] = json.loads(row_dict["componentIds"])
                except (json.JSONDecodeError, TypeError):
                    pass

            results.append(Build(**row_dict))

        return results
    finally:
        conn.close()
