import json
import hashlib
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import get_now_iso_from_data
except ImportError:
    from utils import get_now_iso_from_data


class ProcessCustomerIssue(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        customer_id: str,
        issue_type: str,
        order_id: Optional[str] = None,
        auto_escalate: bool = False,
    ) -> str:
        """Workflow tool: Create ticket, determine priority, optionally auto-escalate based on issue type."""
        # Validate customer
        customer_table = data.get("customer", {})
        if not isinstance(customer_table, dict) or customer_id not in customer_table:
            return json.loads(json.dumps({"error": f"Customer {customer_id} not found"}))

        customer = customer_table[customer_id]

        # Validate order if provided
        if order_id:
            order_table = data.get("order", {})
            if not isinstance(order_table, dict) or order_id not in order_table:
                return json.loads(json.dumps({"error": f"Order {order_id} not found"}))

        # Determine priority based on issue type and customer loyalty
        priority_map = {
            "damaged_product": "high",
            "defective_item": "high",
            "missing_items": "high",
            "wrong_item": "medium",
            "shipping_delay": "medium",
            "billing_question": "medium",
            "general_inquiry": "low",
        }
        priority = priority_map.get(issue_type, "medium")

        # Boost priority for high-value customers
        loyalty_tier = customer.get("loyaltyTier", "").lower()
        if loyalty_tier in ["gold", "platinum"] and priority == "medium":
            priority = "high"

        # Generate ticket ID
        id_input = f"{customer_id}|{issue_type}|{get_now_iso_from_data(data)}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        ticket_id = f"ticket_{id_hash}"

        # Create ticket
        ticket = {
            "id": ticket_id,
            "type": "support_ticket",
            "customerId": customer_id,
            "orderId": order_id,
            "subject": f"{issue_type.replace('_', ' ').title()} - {customer.get('name')}",
            "status": "open",
            "priority": priority,
            "ticketType": issue_type,
            "createdAt": get_now_iso_from_data(data),
            "updatedAt": get_now_iso_from_data(data),
        }

        # Store ticket
        if "support_ticket" not in data or not isinstance(data["support_ticket"], dict):
            data["support_ticket"] = {}
        data["support_ticket"][ticket_id] = ticket

        # Auto-escalate if requested or if high priority + specific issue types
        escalation = None
        should_escalate = auto_escalate or (
            priority == "high" and issue_type in ["damaged_product", "defective_item"]
        )

        if should_escalate:
            # Create escalation
            esc_id_input = f"{ticket_id}|technical|{get_now_iso_from_data(data)}"
            esc_id_hash = hashlib.sha256(esc_id_input.encode()).hexdigest()[:12]
            escalation_id = f"esc_{esc_id_hash}"

            escalation = {
                "id": escalation_id,
                "type": "escalation",
                "ticketId": ticket_id,
                "escalationType": "technical" if issue_type in ["defective_item", "damaged_product"] else "policy_exception",
                "destination": "product_specialist_team",
                "notes": f"Auto-escalated due to {issue_type}",
                "createdAt": get_now_iso_from_data(data),
                "resolvedAt": None,
            }

            if "escalation" not in data or not isinstance(data["escalation"], dict):
                data["escalation"] = {}
            data["escalation"][escalation_id] = escalation

        return json.loads(json.dumps({
            "success": True,
            "ticket": ticket,
            "escalation": escalation,
            "auto_escalated": escalation is not None,
            "priority": priority,
            "message": f"Issue processed: Ticket {ticket_id} created with {priority} priority" +
                      (f" and escalated to {escalation['destination']}" if escalation else ""),
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "process_customer_issue",
                "description": "Workflow tool: Create support ticket with auto-determined priority based on issue type and customer tier. Optionally auto-escalates high-priority issues. **When auto_escalate=True, this tool automatically creates an escalation entity** - this is the primary way to create escalations (there is no separate create_escalation tool). **CRITICAL: Verify all parameters (customer_id, issue_type, order_id, auto_escalate) are correct before calling. Ticket entities cannot be deleted once created.**",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID reporting the issue.",
                        },
                        "issue_type": {
                            "type": "string",
                            "description": "Type of issue: damaged_product, defective_item, missing_items, wrong_item, shipping_delay, billing_question, general_inquiry.",
                        },
                        "order_id": {
                            "type": "string",
                            "description": "Optional order ID if issue relates to an order.",
                        },
                        "auto_escalate": {
                            "type": "boolean",
                            "description": "When true, creates an escalation entity automatically. This is THE way to create escalations - there is no separate create_escalation tool. Use this when you need to escalate a ticket to specialists or management (default: false).",
                        },
                    },
                    "required": ["customer_id", "issue_type"],
                },
            },
        }
