import uuid
from typing import Annotated, Optional
from pydantic import Field
from utils import get_db_conn
from models import Escalation


def createEscalation(
    ticket_id: Annotated[
        str,
        Field(description="The support ticket ID to escalate")
    ],
    escalation_type: Annotated[
        str,
        Field(description="Type of escalation. Valid values: 'technical', 'policy_exception', 'product_specialist'")
    ],
    destination: Annotated[
        str,
        Field(description="Destination for escalation (employee ID or department name)")
    ],
    notes: Annotated[
        Optional[str],
        Field(description="Notes about the escalation (optional)")
    ] = None,
) -> Escalation:
    """Create an escalation for a support ticket"""

    # Validate escalation type enum
    valid_types = ['technical', 'policy_exception', 'product_specialist']
    if escalation_type not in valid_types:
        raise ValueError(f"Invalid escalation_type: {escalation_type}. Must be one of: {', '.join(valid_types)}")

    # Generate escalation ID
    escalation_id = f"esc-{uuid.uuid4()}"

    conn = get_db_conn()

    try:
        cursor = conn.cursor()

        # Verify ticket exists
        cursor.execute("SELECT id FROM SupportTicket WHERE id = ?", (ticket_id,))
        if not cursor.fetchone():
            raise ValueError(f"Ticket {ticket_id} not found")

        # Insert escalation
        sql = """
            INSERT INTO Escalation (
                id, type, ticketId, escalationType,
                destination, notes, createdAt, resolvedAt
            ) VALUES (
                ?, 'escalation', ?, ?, ?, ?, datetime('now'), NULL
            )
        """

        params = (escalation_id, ticket_id, escalation_type, destination, notes)
        cursor.execute(sql, params)

        conn.commit()

        # Fetch and return the created escalation
        cursor.execute("SELECT * FROM Escalation WHERE id = ?", (escalation_id,))
        row = cursor.fetchone()

        if row:
            return Escalation(**dict(row))
        else:
            raise ValueError(f"Failed to retrieve created escalation {escalation_id}")

    finally:
        conn.close()