from typing import Annotated
from pydantic import Field
from utils import get_db_conn
from models import Order


def updateOrderStatus(
    order_id: Annotated[
        str,
        Field(description="The order ID to update")
    ],
    status: Annotated[
        str,
        Field(description="New order status. Valid values: 'pending', 'paid', 'fulfilled', 'cancelled', 'backorder', 'refunded', 'partially_refunded'")
    ],
) -> Order:
    """Update the status of an order"""

    # Validate status enum
    valid_statuses = ['pending', 'paid', 'fulfilled', 'cancelled', 'backorder', 'refunded', 'partially_refunded']
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")

    conn = get_db_conn()

    try:
        cursor = conn.cursor()

        sql = """
            UPDATE "Order"
            SET status = ?, updatedAt = datetime('now')
            WHERE id = ?
        """

        cursor.execute(sql, (status, order_id))

        if cursor.rowcount == 0:
            raise ValueError(f"Order {order_id} not found")

        conn.commit()

        # Fetch and return the updated order
        cursor.execute('SELECT * FROM "Order" WHERE id = ?', (order_id,))
        row = cursor.fetchone()

        if row:
            return Order(**dict(row))
        else:
            raise ValueError(f"Failed to retrieve updated order {order_id}")

    finally:
        conn.close()