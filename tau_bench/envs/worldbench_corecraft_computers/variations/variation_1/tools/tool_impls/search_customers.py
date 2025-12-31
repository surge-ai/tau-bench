import json
from typing import Annotated, List, Optional

from ..models import Customer
from pydantic import Field
from .utils import (get_db_conn, parse_datetime_to_timestamp,
                   validate_date_format)


def searchCustomers(
    customer_id: Annotated[
        Optional[str],
        Field(description="Exact customer ID match")
    ] = None,
    name: Annotated[Optional[str], Field(description="Partial name search (case insensitive)")] = None,
    email: Annotated[Optional[str], Field(description="Exact email address match")] = None,
    phone: Annotated[Optional[str], Field(description="Exact phone number match")] = None,
    loyalty_tier: Annotated[
        Optional[str],
        Field(description="Customer loyalty tier. Valid values: \"none\", \"silver\", \"gold\", \"platinum\"")
    ] = None,
    address_text: Annotated[
        Optional[str],
        Field(description="Text search across all address fields (city, region, postal code, street address, etc.)")
    ] = None,
    created_after: Annotated[
        Optional[str],
        Field(description="Filter customers created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")")
    ] = None,
    created_before: Annotated[
        Optional[str],
        Field(description="Filter customers created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")")
    ] = None,
    limit: Annotated[
        Optional[float],
        Field(description="Maximum number of results (default 50, max 200)"),
    ] = None,
) -> List[Customer]:
    """Search for customers"""
    # Validate date formats
    if created_after:
        created_after = validate_date_format(created_after, "created_after")
    if created_before:
        created_before = validate_date_format(created_before, "created_before")
    
    limit = int(limit) if limit else 50
    limit = min(limit, 200)

    conditions = []
    params = []

    if customer_id:
        conditions.append("id = ?")
        params.append(customer_id)

    if email:
        conditions.append("email = ?")
        params.append(email)

    if name:
        conditions.append("name LIKE ?")
        params.append(f"%{name}%")

    if loyalty_tier:
        conditions.append("loyaltyTier = ?")
        params.append(loyalty_tier)

    if address_text:
        conditions.append("addresses LIKE ?")
        params.append(f"%{address_text}%")

    if phone:
        conditions.append("phone = ?")
        params.append(phone)

    if created_after:
        conditions.append("createdAt >= ?")
        params.append(parse_datetime_to_timestamp(created_after))

    if created_before:
        conditions.append("createdAt <= ?")
        params.append(parse_datetime_to_timestamp(created_before))

    params.append(limit)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM Customer {where_clause} ORDER BY name ASC, id ASC LIMIT ?"

    conn = get_db_conn()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)

            # Parse JSON fields
            if "addresses" in row_dict and isinstance(row_dict["addresses"], str):
                try:
                    row_dict["addresses"] = json.loads(row_dict["addresses"])
                except (json.JSONDecodeError, TypeError):
                    pass

            results.append(Customer(**row_dict))

        return results
    finally:
        conn.close()
