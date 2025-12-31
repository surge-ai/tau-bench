from typing import Annotated, Optional
from pydantic import Field
from utils import get_db_conn
from models import SupportTicket, Priority, Status1 as TicketStatus


def updateTicketStatus(
    ticket_id: Annotated[
        str,
        Field(description="The support ticket ID to update")
    ],
    status: Annotated[
        Optional[str],
        Field(description="New ticket status. Valid values: 'new', 'open', 'pending_customer', 'resolved', 'closed'")
    ] = None,
    assigned_employee_id: Annotated[
        Optional[str],
        Field(description="Employee ID to assign the ticket to")
    ] = None,
    priority: Annotated[
        Optional[str],
        Field(description="Ticket priority. Valid values: 'low', 'normal', 'high'")
    ] = None,
) -> SupportTicket:
    """Update the status, assignment, and priority of a support ticket"""

    # Validate enums
    if status and status not in ['new', 'open', 'pending_customer', 'resolved', 'closed']:
        raise ValueError(f"Invalid status: {status}")

    if priority and priority not in ['low', 'normal', 'high']:
        raise ValueError(f"Invalid priority: {priority}")

    conn = get_db_conn()

    try:
        cursor = conn.cursor()

        # Build UPDATE statement dynamically based on provided fields
        updates = []
        params = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if assigned_employee_id is not None:
            updates.append("assignedEmployeeId = ?")
            params.append(assigned_employee_id)

        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)

        if not updates:
            raise ValueError("No fields to update")

        # Add updatedAt
        updates.append("updatedAt = datetime('now')")

        # Add ticket_id at the end for WHERE clause
        params.append(ticket_id)

        sql = f"""
            UPDATE SupportTicket
            SET {', '.join(updates)}
            WHERE id = ?
        """

        cursor.execute(sql, params)

        if cursor.rowcount == 0:
            raise ValueError(f"Ticket {ticket_id} not found")

        conn.commit()

        # Fetch and return the updated ticket
        cursor.execute("SELECT * FROM SupportTicket WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()

        if row:
            return SupportTicket(**dict(row))
        else:
            raise ValueError(f"Failed to retrieve updated ticket {ticket_id}")

    finally:
        conn.close()