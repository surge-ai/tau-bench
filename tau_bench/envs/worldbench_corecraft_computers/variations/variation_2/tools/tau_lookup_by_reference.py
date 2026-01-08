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
            for customer in customer_table.values():
                if isinstance(customer, dict):
                    email = customer.get("email", "").lower()
                    phone = customer.get("phone", "").lower()
                    name = customer.get("name", "").lower()
                    if (reference_lower in email or
                        reference_lower in phone or
                        reference_lower in name or
                        customer.get("id") == reference):
                        results["customers"].append(customer)

        # Search orders by ID or order number
        order_table = data.get("order", {})
        if isinstance(order_table, dict):
            for order in order_table.values():
                if isinstance(order, dict):
                    order_id = order.get("id", "").lower()
                    order_number = str(order.get("orderNumber", "")).lower()
                    if reference_lower in order_id or reference_lower in order_number:
                        results["orders"].append(order)

        # Search tickets by ID or subject
        ticket_table = data.get("support_ticket", {})
        if isinstance(ticket_table, dict):
            for ticket in ticket_table.values():
                if isinstance(ticket, dict):
                    ticket_id = ticket.get("id", "").lower()
                    subject = ticket.get("subject", "").lower()
                    if reference_lower in ticket_id or reference_lower in subject:
                        results["tickets"].append(ticket)

        # Search employees by email or name
        employee_table = data.get("employee", {})
        if isinstance(employee_table, dict):
            for employee in employee_table.values():
                if isinstance(employee, dict):
                    email = employee.get("email", "").lower()
                    name = employee.get("name", "").lower()
                    if reference_lower in email or reference_lower in name or employee.get("id") == reference:
                        results["employees"].append(employee)

        total_results = sum(len(v) for v in results.values())
        return json.dumps({
            "results": results,
            "total_count": total_results,
            "query": reference,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "lookup_by_reference",
                "description": "Search across multiple entity types using a reference identifier (email, phone, order number, name, ID, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reference": {
                            "type": "string",
                            "description": "Reference identifier to search for (email, phone number, order number, name, ID, etc.).",
                        },
                    },
                    "required": ["reference"],
                },
            },
        }
