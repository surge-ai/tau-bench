from typing import Annotated, Any, Dict, Optional

from pydantic import Field
from utils import (get_db_conn, parse_datetime_to_timestamp,
                   timestamp_to_iso_string, validate_date_format)


def getCustomerTicketHistory(
    customer_id: Annotated[str, Field(description="The customer_id parameter")],
    include_resolved: Annotated[
        Optional[str],
        Field(description="Include resolved/closed tickets (default: true)")
    ] = None,
    tkt_created_after: Annotated[
        Optional[str],
        Field(description="Filter tickets created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")")
    ] = None,
    tkt_created_before: Annotated[
        Optional[str],
        Field(description="Filter tickets created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")")
    ] = None,
    tkt_updated_after: Annotated[
        Optional[str],
        Field(description="Filter tickets updated after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")")
    ] = None,
    tkt_updated_before: Annotated[
        Optional[str],
        Field(description="Filter tickets updated before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")")
    ] = None,
) -> Dict[str, Any]:
    """Get customer ticket history with escalations and resolutions"""
    if not customer_id:
        raise ValueError("customer_id is required")
    
    # Validate date formats
    if tkt_created_after:
        tkt_created_after = validate_date_format(tkt_created_after, "tkt_created_after")
    if tkt_created_before:
        tkt_created_before = validate_date_format(tkt_created_before, "tkt_created_before")
    if tkt_updated_after:
        tkt_updated_after = validate_date_format(tkt_updated_after, "tkt_updated_after")
    if tkt_updated_before:
        tkt_updated_before = validate_date_format(tkt_updated_before, "tkt_updated_before")
    
    include_resolved_bool = include_resolved != "false" if include_resolved else True

    conn = get_db_conn()

    try:
        cursor = conn.cursor()

        # Build ticket query
        conditions = ["customerId = ?"]
        params = [customer_id]

        if not include_resolved_bool:
            conditions.append("status NOT IN ('resolved', 'closed')")

        if tkt_created_after:
            conditions.append("createdAt >= ?")
            params.append(parse_datetime_to_timestamp(tkt_created_after))

        if tkt_created_before:
            conditions.append("createdAt < ?")
            params.append(parse_datetime_to_timestamp(tkt_created_before))

        if tkt_updated_after:
            conditions.append("updatedAt >= ?")
            params.append(parse_datetime_to_timestamp(tkt_updated_after))

        if tkt_updated_before:
            conditions.append("updatedAt < ?")
            params.append(parse_datetime_to_timestamp(tkt_updated_before))

        where_clause = " AND ".join(conditions)
        sql = f"SELECT * FROM SupportTicket WHERE {where_clause} ORDER BY createdAt DESC, id ASC"

        cursor.execute(sql, params)
        ticket_rows = cursor.fetchall()

        tickets = []
        ticket_ids = []
        for row in ticket_rows:
            ticket_dict = dict(row)
            # Format tickets to match reference output (simplified with category)
            formatted_ticket = {
                "id": ticket_dict["id"],
                "customerId": ticket_dict["customerId"],
                "category": ticket_dict["ticketType"],  # Map ticketType to category
                "status": ticket_dict["status"],
                "priority": ticket_dict["priority"],
                "subject": ticket_dict["subject"],
                "createdAt": timestamp_to_iso_string(ticket_dict["createdAt"]),
                "updatedAt": timestamp_to_iso_string(ticket_dict["updatedAt"]),
            }
            tickets.append(formatted_ticket)
            ticket_ids.append(ticket_dict["id"])

        # Get escalations for these tickets
        escalations = []
        resolutions = []

        if ticket_ids:
            placeholders = ",".join("?" * len(ticket_ids))

            # Get escalations
            cursor.execute(
                f"SELECT * FROM Escalation WHERE ticketId IN ({placeholders})",
                ticket_ids
            )
            escalation_rows = cursor.fetchall()
            for row in escalation_rows:
                e_dict = dict(row)
                escalations.append({
                    "id": e_dict["id"],
                    "ticketId": e_dict["ticketId"],
                    "escalation_type": e_dict["escalationType"],
                    "destination": e_dict["destination"],
                })

            # Get resolutions
            cursor.execute(
                f"SELECT * FROM Resolution WHERE ticketId IN ({placeholders})",
                ticket_ids
            )
            resolution_rows = cursor.fetchall()
            for row in resolution_rows:
                r_dict = dict(row)
                resolutions.append({
                    "id": r_dict["id"],
                    "ticketId": r_dict["ticketId"],
                    "outcome": r_dict["outcome"],
                    "details": r_dict["details"],
                })

        return {
            "tickets": tickets,
            "escalations": escalations,
            "resolutions": resolutions
        }
    finally:
        conn.close()
