import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool


class CalculateOrderTotals(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        product_ids: List[str],
        quantities: Optional[List[int]] = None,
        customer_id: Optional[str] = None,
        promo_code: Optional[str] = None,
        shipping_method: Optional[str] = None,
        tax_rate: Optional[float] = None,
    ) -> str:
        """Calculate comprehensive order totals including subtotal, discounts, taxes, and shipping."""
        if quantities is None:
            quantities = [1] * len(product_ids)

        if len(product_ids) != len(quantities):
            return json.loads(json.dumps({"error": "product_ids and quantities must have same length"}))

        product_table = data.get("product", {})
        if not isinstance(product_table, dict):
            return json.loads(json.dumps({"error": "Product data not available"}))

        # Calculate subtotal
        subtotal = 0.0
        items = []
        total_weight = 0.0

        for pid, qty in zip(product_ids, quantities):
            product = product_table.get(pid)
            if not product:
                continue

            price = float(product.get("price", 0))
            weight = float(product.get("weight", 0))
            item_total = price * qty

            items.append({
                "product_id": pid,
                "name": product.get("name"),
                "quantity": qty,
                "unit_price": price,
                "item_total": round(item_total, 2),
            })

            subtotal += item_total
            total_weight += weight * qty

        # Apply customer loyalty discount
        loyalty_discount = 0.0
        loyalty_tier = None
        if customer_id:
            customer_table = data.get("customer", {})
            if isinstance(customer_table, dict) and customer_id in customer_table:
                customer = customer_table[customer_id]
                loyalty_tier = customer.get("loyaltyTier", "").lower()
                discount_rates = {
                    "silver": 0.05,
                    "gold": 0.10,
                    "platinum": 0.15,
                }
                loyalty_discount = subtotal * discount_rates.get(loyalty_tier, 0)

        # Apply promo code discount (flat 10% for simplicity)
        promo_discount = 0.0
        if promo_code:
            promo_discount = subtotal * 0.10

        # Calculate total discount
        total_discount = loyalty_discount + promo_discount

        # Calculate subtotal after discount
        discounted_subtotal = subtotal - total_discount

        # Calculate tax
        if tax_rate is None:
            tax_rate = 0.08  # Default 8%
        tax = discounted_subtotal * tax_rate

        # Calculate shipping based on method and weight
        shipping_rates = {
            "standard": 9.99,
            "express": 19.99,
            "overnight": 39.99,
            "free": 0.00,
        }
        base_shipping = shipping_rates.get((shipping_method or "standard").lower(), 9.99)

        # Add weight-based shipping surcharge
        if total_weight > 10:
            base_shipping += (total_weight - 10) * 0.50

        shipping = base_shipping

        # Calculate total
        total = discounted_subtotal + tax + shipping

        result = {
            "items": items,
            "subtotal": round(subtotal, 2),
            "discounts": {
                "loyalty": round(loyalty_discount, 2),
                "loyalty_tier": loyalty_tier,
                "promo": round(promo_discount, 2),
                "promo_code": promo_code,
                "total": round(total_discount, 2),
            },
            "discounted_subtotal": round(discounted_subtotal, 2),
            "tax": round(tax, 2),
            "tax_rate": tax_rate,
            "shipping": round(shipping, 2),
            "shipping_method": shipping_method or "standard",
            "total_weight": round(total_weight, 2),
            "grand_total": round(total, 2),
        }

        return json.loads(json.dumps(result))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "calculate_order_totals",
                "description": "Calculate comprehensive order totals including subtotal, loyalty/promo discounts, taxes, weight-based shipping, and grand total.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of product IDs.",
                        },
                        "quantities": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Quantities for each product (default: 1 each).",
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID to apply loyalty discounts.",
                        },
                        "promo_code": {
                            "type": "string",
                            "description": "Promotional code to apply discount.",
                        },
                        "shipping_method": {
                            "type": "string",
                            "description": "Shipping method: standard, express, overnight, or free.",
                        },
                        "tax_rate": {
                            "type": "number",
                            "description": "Tax rate as decimal (default: 0.08 for 8%).",
                        },
                    },
                    "required": ["product_ids"],
                },
            },
        }
