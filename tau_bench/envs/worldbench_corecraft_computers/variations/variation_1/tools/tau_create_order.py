import json
import hashlib
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import get_entity_by_id, validate_enum


# Valid enum values
VALID_STATUSES = ["pending", "paid", "fulfilled", "cancelled", "backorder", "refunded", "partially_refunded"]
VALID_CARRIERS = ["UPS Ground", "USPS Ground", "FedEx Express", "FedEx Overnight"]
VALID_SERVICES = ["standard", "express", "overnight"]


def _now_iso_from_data(data: Dict[str, Any]) -> str:
    """Deterministic-ish timestamp.

    If your env provides a fixed clock string in `data` (e.g. data['now'] or data['__now']),
    we use it. Otherwise we return a constant to keep eval deterministic.
    """
    for k in ("__now", "now", "current_time", "currentTime"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return "1970-01-01T00:00:00Z"


class CreateOrder(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        customer_id: str,
        line_items: List[Dict[str, Any]],
        status: Optional[str] = "pending",
        shipping_address: Optional[Dict[str, Any]] = None,
        shipping_carrier: Optional[str] = None,
        shipping_service: Optional[str] = None,
        build_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new order for a customer.

        Persisted fields:
          - id: ord_<hash>
          - customerId
          - lineItems (list of {productId, qty})
          - status
          - shipping (optional, contains address, carrier, service)
          - buildId (optional)
          - createdAt
          - updatedAt
        """
        # Validate enum parameters
        validate_enum(status, VALID_STATUSES, "status")
        validate_enum(shipping_carrier, VALID_CARRIERS, "shipping_carrier")
        validate_enum(shipping_service, VALID_SERVICES, "shipping_service")

        # Validate customer exists
        if not get_entity_by_id(data, "customer", customer_id):
            raise ValueError(f"Customer {customer_id} not found")

        # Validate all product IDs in line items exist
        if not line_items:
            raise ValueError("Order must have at least one line item")

        product_ids = [item.get("productId") or item.get("product_id") for item in line_items]
        not_found = [pid for pid in product_ids if pid and not get_entity_by_id(data, "product", pid)]
        if not_found:
            raise ValueError(f"Products not found: {', '.join(not_found)}")

        # Validate line items have required fields
        for i, item in enumerate(line_items):
            product_id = item.get("productId") or item.get("product_id")
            qty = item.get("qty") or item.get("quantity")
            if not product_id:
                raise ValueError(f"Line item {i} missing productId")
            if not qty or qty < 1:
                raise ValueError(f"Line item {i} must have qty >= 1")

        # Validate build exists if provided
        if build_id and not get_entity_by_id(data, "build", build_id):
            raise ValueError(f"Build {build_id} not found")

        # Normalize line items to consistent format
        normalized_items = []
        for item in line_items:
            product_id = item.get("productId") or item.get("product_id")
            qty = item.get("qty") or item.get("quantity")
            normalized_items.append({"productId": product_id, "qty": int(qty)})

        # Generate deterministic ID based on input parameters
        items_str = "|".join(f"{i['productId']}:{i['qty']}" for i in sorted(normalized_items, key=lambda x: x['productId']))
        id_input = f"{customer_id}|{items_str}|{status or 'pending'}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        order_id = f"ord_{id_hash}"

        now = _now_iso_from_data(data)
        row: Dict[str, Any] = {
            "id": order_id,
            "customerId": customer_id,
            "lineItems": normalized_items,
            "status": status or "pending",
            "createdAt": now,
            "updatedAt": now,
        }

        # Add optional shipping info
        if shipping_address or shipping_carrier or shipping_service:
            row["shipping"] = {}
            if shipping_address:
                row["shipping"]["address"] = shipping_address
            if shipping_carrier:
                row["shipping"]["carrier"] = shipping_carrier
            if shipping_service:
                row["shipping"]["service"] = shipping_service

        # Add optional build reference
        if build_id:
            row["buildId"] = build_id

        # Use dictionary format keyed by ID
        if "order" not in data or not isinstance(data["order"], dict):
            data["order"] = {}
        data["order"][order_id] = row

        return json.loads(json.dumps(row))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "createOrder",
                "description": "Create a new order for a customer. An order contains line items (products and quantities), shipping information, and status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The ID of the customer placing the order.",
                        },
                        "line_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "productId": {"type": "string", "description": "The product ID."},
                                    "qty": {"type": "integer", "description": "The quantity ordered."},
                                },
                                "required": ["productId", "qty"],
                            },
                            "description": "List of products and quantities in the order.",
                        },
                        "status": {
                            "type": "string",
                            "enum": VALID_STATUSES,
                            "description": "The order status (default: pending).",
                        },
                        "shipping_address": {
                            "type": "object",
                            "properties": {
                                "line1": {"type": "string", "description": "Street address."},
                                "line2": {"type": "string", "description": "Apartment/unit number (optional)."},
                                "city": {"type": "string", "description": "City name."},
                                "region": {"type": "string", "description": "State/province code."},
                                "postalCode": {"type": "string", "description": "ZIP/postal code."},
                                "country": {"type": "string", "description": "Country code (e.g., US, CA)."},
                            },
                            "description": "The shipping address for the order.",
                        },
                        "shipping_carrier": {
                            "type": "string",
                            "enum": VALID_CARRIERS,
                            "description": "The shipping carrier.",
                        },
                        "shipping_service": {
                            "type": "string",
                            "enum": VALID_SERVICES,
                            "description": "The shipping service level.",
                        },
                        "build_id": {
                            "type": "string",
                            "description": "Optional reference to a custom build configuration.",
                        },
                    },
                    "required": ["customer_id", "line_items"],
                },
            },
        }
