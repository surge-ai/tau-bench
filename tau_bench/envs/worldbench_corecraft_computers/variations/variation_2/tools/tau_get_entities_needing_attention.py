import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class GetEntitiesNeedingAttention(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any]) -> str:
        """Get all entities that need attention: pending refunds, open tickets, failed payments, etc."""
        results: Dict[str, List[Dict[str, Any]]] = {
            "open_tickets": [],
            "urgent_tickets": [],
            "pending_refunds": [],
            "failed_payments": [],
            "pending_escalations": [],
            "unresolved_tickets": [],
            "cancelled_orders": [],
        }

        # Open tickets
        ticket_table = data.get("support_ticket", {})
        if isinstance(ticket_table, dict):
            for ticket in ticket_table.values():
                if isinstance(ticket, dict):
                    status = ticket.get("status", "").lower()
                    priority = ticket.get("priority", "").lower()

                    if status in ["new", "open", "pending_customer"]:
                        results["open_tickets"].append(ticket)

                        if priority in ["high", "urgent"]:
                            results["urgent_tickets"].append(ticket)

                    if status not in ["resolved", "closed"]:
                        results["unresolved_tickets"].append(ticket)

        # Pending refunds
        refund_table = data.get("refund", {})
        if isinstance(refund_table, dict):
            for refund in refund_table.values():
                if isinstance(refund, dict) and refund.get("status", "").lower() == "pending":
                    results["pending_refunds"].append(refund)

        # Failed payments
        payment_table = data.get("payment", {})
        if isinstance(payment_table, dict):
            for payment in payment_table.values():
                if isinstance(payment, dict) and payment.get("status", "").lower() == "failed":
                    results["failed_payments"].append(payment)

        # Pending escalations
        escalation_table = data.get("escalation", {})
        if isinstance(escalation_table, dict):
            for escalation in escalation_table.values():
                if isinstance(escalation, dict):
                    status = escalation.get("status", "").lower()
                    if status == "pending" or not escalation.get("resolvedAt"):
                        results["pending_escalations"].append(escalation)

        # Cancelled orders (might need follow-up)
        order_table = data.get("order", {})
        if isinstance(order_table, dict):
            for order in order_table.values():
                if isinstance(order, dict) and order.get("status", "").lower() == "cancelled":
                    results["cancelled_orders"].append(order)

        # Calculate summary counts
        summary = {k: len(v) for k, v in results.items()}
        total_items = sum(summary.values())

        return json.loads(json.dumps({
            "results": results,
            "summary": summary,
            "total_items_needing_attention": total_items,
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_entities_needing_attention",
                "description": "Get all entities requiring attention: open/urgent tickets, pending refunds, failed payments, pending escalations, cancelled orders.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        }
