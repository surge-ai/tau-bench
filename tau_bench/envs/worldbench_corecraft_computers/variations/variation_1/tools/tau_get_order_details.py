import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    get_entity_by_id,
    parse_iso_datetime,
    parse_entity_json_fields,
    get_datetime_field,
)


class GetOrderDetails(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: str = None,
        created_before: Optional[str] = None,
        **kwargs,
    ) -> str:
        # Handle order_id passed via kwargs
        if order_id is None:
            order_id = kwargs.get("order_id")

        if not order_id:
            raise ValueError("order_id is required")

        # Parse created_before filter
        created_before_dt = parse_iso_datetime(created_before) if created_before else None

        # Get order
        order = get_entity_by_id(data, "order", order_id)

        if not order:
            return json.dumps({
                "order": None,
                "payment": None,
                "shipment": None,
                "customer": None,
                "tickets": []
            })

        # Parse JSON fields
        order = parse_entity_json_fields(order, ["lineItems", "shipping"])

        # Format order
        formatted_order = {
            "id": order["id"],
            "customer_id": order.get("customerId"),
            "line_items": order.get("lineItems"),
            "status": order.get("status"),
            "created_at": order.get("createdAt", ""),
            "updated_at": order.get("updatedAt", ""),
        }

        # Get customer
        customer = None
        customer_id = order.get("customerId")
        if customer_id:
            cust = get_entity_by_id(data, "customer", customer_id)
            if cust:
                customer = {
                    "name": cust.get("name"),
                    "email": cust.get("email"),
                    "loyalty_tier": cust.get("loyaltyTier")
                }

        # Get payment (most recent before created_before)
        payment = None
        matching_payments: List[Dict[str, Any]] = []
        for p in iter_entities(data, "payment"):
            if p.get("orderId") != order_id:
                continue
            created_at = get_datetime_field(p, "createdAt")
            if created_at is not None and created_before_dt and created_at > created_before_dt:
                continue
            matching_payments.append(p)
        # Sort by createdAt DESC, then id ASC
        matching_payments.sort(key=lambda x: x.get("id", ""))  # Secondary: id ASC
        matching_payments.sort(key=lambda x: x.get("createdAt", "") or "", reverse=True)  # Primary: createdAt DESC
        if matching_payments:
            p = matching_payments[0]
            payment = {
                "id": p.get("id"),
                "amount": p.get("amount"),
                "method": p.get("method"),
                "status": p.get("status")
            }

        # Get shipment (most recent before created_before)
        shipment = None
        matching_shipments: List[Dict[str, Any]] = []
        for s in iter_entities(data, "shipment"):
            if s.get("orderId") != order_id:
                continue
            created_at = get_datetime_field(s, "createdAt")
            if created_at is not None and created_before_dt and created_at > created_before_dt:
                continue
            matching_shipments.append(s)
        # Sort by createdAt DESC, then id ASC
        matching_shipments.sort(key=lambda x: x.get("id", ""))  # Secondary: id ASC
        matching_shipments.sort(key=lambda x: x.get("createdAt", "") or "", reverse=True)  # Primary: createdAt DESC
        if matching_shipments:
            s = matching_shipments[0]
            shipment = {
                "id": s.get("id"),
                "tracking_number": s.get("trackingNumber"),
                "carrier": s.get("carrier"),
                "status": s.get("status")
            }

        # Get tickets (all before created_before)
        tickets: List[Dict[str, Any]] = []
        for t in iter_entities(data, "support_ticket"):
            if t.get("orderId") != order_id:
                continue
            created_at = get_datetime_field(t, "createdAt")
            if created_at is not None and created_before_dt and created_at > created_before_dt:
                continue
            tickets.append({
                "id": t.get("id"),
                "subject": t.get("subject"),
                "status": t.get("status")
            })
        # Sort by createdAt DESC, then id ASC
        tickets.sort(key=lambda x: x.get("id", ""))  # Secondary: id ASC
        tickets.sort(key=lambda x: x.get("createdAt", "") or "", reverse=True)  # Primary: createdAt DESC

        return json.dumps({
            "order": formatted_order,
            "payment": payment,
            "shipment": shipment,
            "customer": customer,
            "tickets": tickets
        }, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "getOrderDetails",
                "description": "Get comprehensive order details including the order itself, associated payment, shipment, customer info, and related support tickets. Returns an object with order, payment, shipment, customer, and tickets fields.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID to retrieve details for"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter related objects (payments, shipments, tickets) to those created before this date, inclusive (ISO 8601 format with UTC timezone, e.g., \"2025-09-01T00:00:00Z\")"
                        }
                    },
                    "required": ["order_id"],
                },
            },
        }
