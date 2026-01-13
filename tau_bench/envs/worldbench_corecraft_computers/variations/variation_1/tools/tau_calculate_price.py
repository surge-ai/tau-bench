import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    get_entity_by_id,
    validate_enum,
)

LOYALTY_TIERS = ["silver", "gold", "platinum"]
SHIPPING_SERVICES = ["standard", "express", "overnight"]


class CalculatePrice(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        product_ids: List[str],
        quantities: Optional[List[int]] = None,
        loyalty_tier: Optional[str] = None,
        shipping_service: Optional[str] = None,
    ) -> str:
        """Calculate subtotal/discount/shipping/total for a list of products."""
        validate_enum(loyalty_tier, LOYALTY_TIERS, "loyalty_tier")
        validate_enum(shipping_service, SHIPPING_SERVICES, "shipping_service")

        if quantities is None:
            quantities = [1] * len(product_ids)

        if len(product_ids) != len(quantities):
            raise ValueError("product_ids and quantities must have same length")

        # Calculate subtotal
        subtotal = 0.0
        missing_ids = []
        for pid, qty in zip(product_ids, quantities):
            product = get_entity_by_id(data, "product", pid)
            if not product:
                missing_ids.append(pid)
                continue
            price = float(product.get("price", 0) or 0)
            subtotal += price * int(qty)
        
        if missing_ids:
            raise ValueError(f"Products not found: {', '.join(missing_ids)}")
        
        # Apply loyalty discount
        discount = 0.0
        if loyalty_tier:
            discounts = {"silver": 0.05, "gold": 0.1, "platinum": 0.15}
            discount = subtotal * discounts.get(loyalty_tier.lower(), 0.0)

        # Shipping
        shipping_rates = {"standard": 9.99, "express": 19.99, "overnight": 39.99}
        shipping = shipping_rates.get((shipping_service or "standard").lower(), 9.99)

        after_discount = subtotal - discount
        total = after_discount + shipping

        result = {
            "subtotal": round(subtotal * 100) / 100,
            "discount": round(discount * 100) / 100,
            "shipping": shipping,
            "total": round(total * 100) / 100,
        }
        return json.dumps(result)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "calculate_price",
                "description": "Calculate price breakdown (subtotal/discount/shipping/total) for a list of product IDs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of product IDs to price.",
                        },
                        "quantities": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Quantities aligned to product_ids. Defaults to 1 each if omitted.",
                        },
                        "loyalty_tier": {
                            "type": "string",
                            "enum": ["silver", "gold", "platinum"],
                            "description": "Optional loyalty tier for discount: silver (5%), gold (10%), or platinum (15%).",
                        },
                        "shipping_service": {
                            "type": "string",
                            "enum": ["standard", "express", "overnight"],
                            "description": "Shipping speed: standard ($9.99), express ($19.99), or overnight ($39.99). Defaults to standard.",
                        },
                    },
                    "required": ["product_ids"],
                },
            },
        }
