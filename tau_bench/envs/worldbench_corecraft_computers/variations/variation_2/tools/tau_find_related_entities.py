import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class FindRelatedEntities(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], entity_id: str) -> str:
        """Given any entity ID, find all entities related to it through foreign key relationships."""
        result: Dict[str, List[Dict[str, Any]]] = {
            "customers": [],
            "orders": [],
            "tickets": [],
            "payments": [],
            "shipments": [],
            "refunds": [],
            "escalations": [],
            "resolutions": [],
            "products": [],
        }

        # Track which entity we found
        source_entity = None
        source_type = None

        # Find the source entity
        for entity_type, data_key in [
            ("customer", "customer"),
            ("order", "order"),
            ("ticket", "support_ticket"),
            ("payment", "payment"),
            ("shipment", "shipment"),
            ("product", "product"),
            ("refund", "refund"),
            ("escalation", "escalation"),
            ("resolution", "resolution"),
        ]:
            table = data.get(data_key, {})
            if isinstance(table, dict) and entity_id in table:
                source_entity = table[entity_id]
                source_type = entity_type
                break

        if not source_entity:
            return json.loads(json.dumps({"error": f"Entity {entity_id} not found", "results": result}))

        # Now find all related entities based on the source type
        customer_id = source_entity.get("customerId")
        order_id = source_entity.get("orderId")
        payment_id = source_entity.get("paymentId")
        ticket_id = source_entity.get("ticketId")

        # If source is customer, get their orders
        if source_type == "customer":
            customer_id = entity_id

        # If source is order, get customer
        if source_type == "order":
            order_id = entity_id

        # Find customer
        if customer_id:
            customer_table = data.get("customer", {})
            if isinstance(customer_table, dict) and customer_id in customer_table:
                result["customers"].append(customer_table[customer_id])

        # Find orders (track IDs as we go)
        order_ids = set()
        if customer_id:
            order_table = data.get("order", {})
            if isinstance(order_table, dict):
                for oid, order in order_table.items():
                    if isinstance(order, dict) and order.get("customerId") == customer_id:
                        result["orders"].append(order)
                        order_ids.add(oid)
        elif order_id:
            order_table = data.get("order", {})
            if isinstance(order_table, dict) and order_id in order_table:
                result["orders"].append(order_table[order_id])
                order_ids.add(order_id)
                # Get customer from this order
                order = order_table[order_id]
                cust_id = order.get("customerId")
                if cust_id:
                    customer_table = data.get("customer", {})
                    if isinstance(customer_table, dict) and cust_id in customer_table:
                        result["customers"].append(customer_table[cust_id])

        # Find tickets (track IDs)
        ticket_ids = set()
        ticket_table = data.get("support_ticket", {})
        if isinstance(ticket_table, dict):
            for tid, ticket in ticket_table.items():
                if isinstance(ticket, dict):
                    if (customer_id and ticket.get("customerId") == customer_id) or \
                       (ticket.get("orderId") in order_ids) or \
                       (ticket_id and tid == ticket_id):
                        result["tickets"].append(ticket)
                        ticket_ids.add(tid)

        # Find payments (track IDs)
        payment_ids = set()
        payment_table = data.get("payment", {})
        if isinstance(payment_table, dict):
            for pid, payment in payment_table.items():
                if isinstance(payment, dict):
                    if (payment.get("orderId") in order_ids) or \
                       (payment_id and pid == payment_id):
                        result["payments"].append(payment)
                        payment_ids.add(pid)

        # Find shipments
        shipment_table = data.get("shipment", {})
        if isinstance(shipment_table, dict):
            for shipment in shipment_table.values():
                if isinstance(shipment, dict) and shipment.get("orderId") in order_ids:
                    result["shipments"].append(shipment)

        # Find refunds
        refund_table = data.get("refund", {})
        if isinstance(refund_table, dict):
            for refund in refund_table.values():
                if isinstance(refund, dict) and refund.get("paymentId") in payment_ids:
                    result["refunds"].append(refund)

        # Find escalations
        escalation_table = data.get("escalation", {})
        if isinstance(escalation_table, dict):
            for escalation in escalation_table.values():
                if isinstance(escalation, dict) and escalation.get("ticketId") in ticket_ids:
                    result["escalations"].append(escalation)

        # Find resolutions
        resolution_table = data.get("resolution", {})
        if isinstance(resolution_table, dict):
            for resolution in resolution_table.values():
                if isinstance(resolution, dict) and resolution.get("ticketId") in ticket_ids:
                    result["resolutions"].append(resolution)

        # Find products (extract from order lineItems)
        all_product_ids = set()
        for order in result["orders"]:
            # Orders have lineItems - may be JSON string or list
            line_items = order.get("lineItems", [])
            if isinstance(line_items, str):
                try:
                    line_items = json.loads(line_items)
                except (json.JSONDecodeError, ValueError):
                    line_items = []

            if isinstance(line_items, list):
                for item in line_items:
                    if isinstance(item, dict) and "productId" in item:
                        all_product_ids.add(item["productId"])

        product_table = data.get("product", {})
        if isinstance(product_table, dict):
            for pid in all_product_ids:
                if pid in product_table:
                    result["products"].append(product_table[pid])

        # Calculate summary
        summary = {k: len(v) for k, v in result.items()}

        return json.loads(json.dumps({
            "source_entity_id": entity_id,
            "source_entity_type": source_type,
            "results": result,
            "summary": summary,
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "find_related_entities",
                "description": "Given any entity ID, traverse relationships to find all connected entities (customers, orders, tickets, payments, shipments, refunds, escalations, resolutions, products).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "ID of any entity (customer, order, ticket, payment, product, etc.).",
                        },
                    },
                    "required": ["entity_id"],
                },
            },
        }
