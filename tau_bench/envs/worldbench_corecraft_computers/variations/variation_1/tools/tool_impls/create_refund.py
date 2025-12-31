import json
import uuid
from typing import Annotated, Optional
from pydantic import Field
from utils import get_db_conn
from models import Refund


def createRefund(
    payment_id: Annotated[
        str,
        Field(description="The payment ID to refund")
    ],
    amount: Annotated[
        float,
        Field(description="Amount to refund")
    ],
    reason: Annotated[
        str,
        Field(description="Reason for refund. Valid values: 'customer_remorse', 'defective', 'incompatible', 'shipping_issue', 'other'")
    ],
    status: Annotated[
        str,
        Field(description="Refund status. Valid values: 'pending', 'approved', 'denied', 'processed', 'failed'")
    ] = "pending",
    ticket_id: Annotated[
        Optional[str],
        Field(description="Associated support ticket ID")
    ] = None,
    lines: Annotated[
        Optional[str],
        Field(description="JSON array of refund line items")
    ] = None,
) -> Refund:
    """Create a new refund for a payment"""

    # Validate enums
    valid_reasons = ['customer_remorse', 'defective', 'incompatible', 'shipping_issue', 'other']
    if reason not in valid_reasons:
        raise ValueError(f"Invalid reason: {reason}. Must be one of: {', '.join(valid_reasons)}")

    valid_statuses = ['pending', 'approved', 'denied', 'processed', 'failed']
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")

    # Generate refund ID
    refund_id = f"ref-{uuid.uuid4()}"

    # Validate lines is valid JSON if provided
    if lines:
        try:
            json.loads(lines)
        except json.JSONDecodeError:
            raise ValueError("lines must be a valid JSON array")

    conn = get_db_conn()

    try:
        cursor = conn.cursor()

        # Verify payment exists
        cursor.execute("SELECT id FROM Payment WHERE id = ?", (payment_id,))
        if not cursor.fetchone():
            raise ValueError(f"Payment {payment_id} not found")

        # Verify ticket exists if provided
        if ticket_id:
            cursor.execute("SELECT id FROM SupportTicket WHERE id = ?", (ticket_id,))
            if not cursor.fetchone():
                raise ValueError(f"Ticket {ticket_id} not found")

        # Set processedAt if status is processed
        processed_at = "datetime('now')" if status == "processed" else "NULL"

        sql = f"""
            INSERT INTO Refund (
                id, type, paymentId, ticketId, amount, reason,
                status, lines, createdAt, processedAt
            ) VALUES (
                ?, 'refund', ?, ?, ?, ?, ?, ?, datetime('now'), {processed_at}
            )
        """

        params = (refund_id, payment_id, ticket_id, amount, reason, status, lines)
        cursor.execute(sql, params)

        conn.commit()

        # Fetch and return the created refund
        cursor.execute("SELECT * FROM Refund WHERE id = ?", (refund_id,))
        row = cursor.fetchone()

        if row:
            row_dict = dict(row)
            # Parse JSON fields
            if "lines" in row_dict and isinstance(row_dict["lines"], str):
                try:
                    row_dict["lines"] = json.loads(row_dict["lines"])
                except (json.JSONDecodeError, TypeError):
                    pass
            return Refund(**row_dict)
        else:
            raise ValueError(f"Failed to retrieve created refund {refund_id}")

    finally:
        conn.close()