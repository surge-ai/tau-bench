import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class LookupByReference(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], reference: str) -> str:
        """Lookup entities by various reference identifiers like email, phone, order number, etc."""
        results: Dict[str, List[Dict[str, Any]]] = {
            "customers": [],
            "orders": [],
            "tickets": [],
            "employees": [],
        }

        reference_lower = reference.lower()

        # Search customers by email, phone, or name
        customer_table = data.get("customer", {})
        if isinstance(customer_table, dict):
            for customer_key, customer in customer_table.items():
                if isinstance(customer, dict):
                    email = (customer.get("email") or "").lower()
                    phone = (customer.get("phone") or "").lower()
                    name = (customer.get("name") or "").lower()
                    customer_key_lower = customer_key.lower()
                    if (reference_lower in email or
                        reference_lower in phone or
                        reference_lower in name or
                        reference_lower in customer_key_lower or
                        customer.get("id") == reference):
                        results["customers"].append(customer)

        # Search orders by ID or order number
        order_table = data.get("order", {})
        if isinstance(order_table, dict):
            for order_key, order in order_table.items():
                if isinstance(order, dict):
                    # Check both the key and any id/orderNumber fields
                    order_id = (order.get("id") or "").lower()
                    order_number = str(order.get("orderNumber") or "").lower()
                    order_key_lower = order_key.lower()
                    if (reference_lower in order_id or
                        reference_lower in order_number or
                        reference_lower in order_key_lower):
                        results["orders"].append(order)

        # Search tickets by ID or subject
        ticket_table = data.get("support_ticket", {})
        if isinstance(ticket_table, dict):
            for ticket_key, ticket in ticket_table.items():
                if isinstance(ticket, dict):
                    ticket_id = (ticket.get("id") or "").lower()
                    subject = (ticket.get("subject") or "").lower()
                    ticket_key_lower = ticket_key.lower()
                    if (reference_lower in ticket_id or
                        reference_lower in subject or
                        reference_lower in ticket_key_lower):
                        results["tickets"].append(ticket)

        # Search employees by email or name
        employee_table = data.get("employee", {})
        if isinstance(employee_table, dict):
            for employee_key, employee in employee_table.items():
                if isinstance(employee, dict):
                    email = (employee.get("email") or "").lower()
                    name = (employee.get("name") or "").lower()
                    employee_key_lower = employee_key.lower()
                    if (reference_lower in email or
                        reference_lower in name or
                        reference_lower in employee_key_lower or
                        employee.get("id") == reference):
                        results["employees"].append(employee)

        total_results = sum(len(v) for v in results.values())
        return json.loads(json.dumps({
            "results": results,
            "total_count": total_results,
            "query": reference,
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "lookup_by_reference",
                "description": "Search across multiple entity types (customers, orders, tickets, employees) by entity IDs or other identifiers. Searches both entity IDs (like 'ord-250830-110', 'tick-250828-001') and entity fields (email, phone, name, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reference": {
                            "type": "string",
                            "description": "Reference identifier to search for. Can be an entity ID (order ID like 'ord-250830-110', ticket ID like 'tick-250828-001', customer ID, employee ID) or other identifiers (email, phone number, name).",
                        },
                    },
                    "required": ["reference"],
                },
            },
        }
