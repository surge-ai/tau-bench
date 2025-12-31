from typing import Annotated, List, Optional

from ..models import SupportTicket
from pydantic import Field
from .utils import (get_db_conn, parse_datetime_to_timestamp,
                   validate_date_format)


def searchTickets(
    ticket_id: Annotated[Optional[str], Field(description="Specific ticket ID to find")] = None,
    customer_id: Annotated[Optional[str], Field(description="Customer ID to filter by")] = None,
    assigned_employee_id: Annotated[Optional[str], Field(description="Employee ID to filter by")] = None,
    status: Annotated[
        Optional[str],
        Field(description="Ticket status to filter by. Valid values: \"new\", \"open\", \"pending_customer\", \"resolved\", \"closed\"")
    ] = None,
    priority: Annotated[
        Optional[str],
        Field(description="Ticket priority to filter by. Valid values: \"low\", \"normal\", \"high\"")
    ] = None,
    ticket_type: Annotated[
        Optional[str],
        Field(description="Ticket type to filter by. Valid values: \"return\", \"troubleshooting\", \"recommendation\", \"order_issue\", \"shipping\", \"billing\", \"other\"")
    ] = None,
    text: Annotated[Optional[str], Field(description="Text to search in subject and body")] = None,
    created_after: Annotated[
        Optional[str],
        Field(description="Filter tickets created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")")
    ] = None,
    created_before: Annotated[
        Optional[str],
        Field(description="Filter tickets created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")")
    ] = None,
    resolved_after: Annotated[
        Optional[str],
        Field(description="Filter tickets resolved after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-01T00:00:00Z\")")
    ] = None,
    resolved_before: Annotated[
        Optional[str],
        Field(description="Filter tickets resolved before this date (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")")
    ] = None,
    limit: Annotated[
        Optional[float],
        Field(description="Maximum number of results (default 50, max 200)"),
    ] = None,
) -> List[SupportTicket]:
    """Search for support tickets"""
    # Validate date formats
    if created_after:
        created_after = validate_date_format(created_after, "created_after")
    if created_before:
        created_before = validate_date_format(created_before, "created_before")
    if resolved_after:
        resolved_after = validate_date_format(resolved_after, "resolved_after")
    if resolved_before:
        resolved_before = validate_date_format(resolved_before, "resolved_before")
    
    limit = int(limit) if limit else 50
    limit = min(limit, 200)

    conditions = []
    params = []

    if customer_id:
        conditions.append("customerId = ?")
        params.append(customer_id)

    if status:
        conditions.append("status = ?")
        params.append(status)

    if priority:
        conditions.append("priority = ?")
        params.append(priority)

    if ticket_type:
        conditions.append("ticketType = ?")
        params.append(ticket_type)

    if assigned_employee_id:
        conditions.append("assignedEmployeeId = ?")
        params.append(assigned_employee_id)

    if ticket_id:
        conditions.append("id = ?")
        params.append(ticket_id)

    if text:
        conditions.append("(subject LIKE ? OR body LIKE ?)")
        params.extend([f"%{text}%", f"%{text}%"])

    if created_after:
        conditions.append("createdAt >= ?")
        params.append(parse_datetime_to_timestamp(created_after))

    if created_before:
        conditions.append("createdAt <= ?")
        params.append(parse_datetime_to_timestamp(created_before))

    if resolved_after:
        conditions.append("updatedAt >= ?")
        params.append(parse_datetime_to_timestamp(resolved_after))

    if resolved_before:
        conditions.append("updatedAt <= ?")
        params.append(parse_datetime_to_timestamp(resolved_before))

    params.append(limit)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM SupportTicket {where_clause} ORDER BY createdAt DESC, id ASC LIMIT ?"

    conn = get_db_conn()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)
            results.append(SupportTicket(**row_dict))

        # Sort by priority (high -> normal -> low), then by createdAt DESC, then by id ASC
        # This matches the JavaScript implementation's lodash orderBy
        priority_order = {"high": 1, "normal": 2, "low": 3}
        results.sort(
            key=lambda ticket: (
                priority_order.get(ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority, 4),  # Priority first
                -ticket.createdAt.timestamp() if ticket.createdAt else 0,  # Then createdAt DESC (negative for descending)
                ticket.id  # Then id ASC
            )
        )

        return results
    finally:
        conn.close()
