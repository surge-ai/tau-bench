import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class AnalyzeCustomerValue(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], customer_id: str) -> str:
        """Analyze customer value metrics: LTV, order frequency, average order value, support interactions."""
        customer_table = data.get("customer", {})
        if not isinstance(customer_table, dict) or customer_id not in customer_table:
            return json.loads(json.dumps({"error": f"Customer {customer_id} not found"}))

        customer = customer_table[customer_id]

        # Get all orders for this customer
        order_table = data.get("order", {})
        customer_orders = []
        if isinstance(order_table, dict):
            for order in order_table.values():
                if isinstance(order, dict) and order.get("customerId") == customer_id:
                    customer_orders.append(order)

        # Calculate order metrics
        total_orders = len(customer_orders)
        total_revenue = 0.0
        order_statuses = {}

        for order in customer_orders:
            # Calculate total from lineItems (Order model doesn't have a total field)
            line_items = order.get("lineItems", [])
            if isinstance(line_items, str):
                try:
                    line_items = json.loads(line_items)
                except (json.JSONDecodeError, ValueError):
                    line_items = []

            order_total = 0.0
            if isinstance(line_items, list):
                for item in line_items:
                    if isinstance(item, dict):
                        price = float(item.get("price", 0))
                        qty = int(item.get("qty", 1))
                        order_total += price * qty

            total_revenue += order_total

            # Count statuses
            status = order.get("status", "unknown")
            order_statuses[status] = order_statuses.get(status, 0) + 1

        # Note: average_order_value uses gross revenue (before refunds) as it represents average order size
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0

        # Get payment information
        payment_table = data.get("payment", {})
        total_paid = 0.0
        payment_methods = {}
        if isinstance(payment_table, dict):
            order_ids = {order.get("id") for order in customer_orders}
            for payment in payment_table.values():
                if isinstance(payment, dict) and payment.get("orderId") in order_ids:
                    amount = float(payment.get("amount", 0))
                    total_paid += amount
                    method = payment.get("method", "unknown")
                    payment_methods[method] = payment_methods.get(method, 0) + 1

        # Get refund information
        refund_table = data.get("refund", {})
        total_refunded = 0.0
        refund_count = 0
        if isinstance(refund_table, dict):
            order_ids = {order.get("id") for order in customer_orders}
            for refund in refund_table.values():
                if isinstance(refund, dict) and refund.get("orderId") in order_ids:
                    amount = float(refund.get("amount", 0))
                    total_refunded += amount
                    refund_count += 1

        # Calculate net revenue after refunds
        net_revenue = total_revenue - total_refunded

        # Get support ticket metrics
        ticket_table = data.get("support_ticket", {})
        customer_tickets = []
        open_tickets = 0
        resolved_tickets = 0
        if isinstance(ticket_table, dict):
            for ticket in ticket_table.values():
                if isinstance(ticket, dict) and ticket.get("customerId") == customer_id:
                    customer_tickets.append(ticket)
                    status = ticket.get("status", "").lower()
                    if status in ["new", "open", "pending_customer"]:
                        open_tickets += 1
                    elif status in ["resolved", "closed"]:
                        resolved_tickets += 1

        # Calculate customer lifetime value (simple version)
        # LTV uses net revenue to account for returns
        # LTV = (net_revenue / total_orders) * total_orders * estimated_retention_factor
        retention_factor = 1.5  # Simplified assumption
        net_average_order_value = net_revenue / total_orders if total_orders > 0 else 0.0
        estimated_ltv = net_average_order_value * total_orders * retention_factor

        result = {
            "customer_id": customer_id,
            "customer_name": customer.get("name"),
            "loyalty_tier": customer.get("loyaltyTier"),
            "metrics": {
                "total_orders": total_orders,
                "gross_revenue": round(total_revenue, 2),
                "total_refunded": round(total_refunded, 2),
                "net_revenue": round(net_revenue, 2),
                "refund_count": refund_count,
                "total_paid": round(total_paid, 2),
                "average_order_value": round(average_order_value, 2),
                "net_average_order_value": round(net_average_order_value, 2),
                "estimated_lifetime_value": round(estimated_ltv, 2),
            },
            "order_breakdown": order_statuses,
            "payment_methods": payment_methods,
            "support": {
                "total_tickets": len(customer_tickets),
                "open_tickets": open_tickets,
                "resolved_tickets": resolved_tickets,
            },
            "customer_segment": _determine_segment(net_revenue, total_orders, len(customer_tickets)),
        }

        return json.loads(json.dumps(result))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "analyze_customer_value",
                "description": "Analyze customer value metrics including lifetime value, order frequency, average order value, and support interactions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID to analyze.",
                        },
                    },
                    "required": ["customer_id"],
                },
            },
        }


def _determine_segment(revenue: float, orders: int, tickets: int) -> str:
    """Determine customer segment based on metrics."""
    if revenue > 5000 and tickets < 2:
        return "high_value_low_maintenance"
    elif revenue > 5000 and tickets >= 2:
        return "high_value_high_maintenance"
    elif revenue > 1000:
        return "medium_value"
    elif orders > 5:
        return "frequent_buyer"
    elif tickets > 3:
        return "high_support_needs"
    else:
        return "new_or_low_engagement"
