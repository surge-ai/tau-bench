import json
import sqlite3
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .tau_sqlite_utils import build_sqlite_from_data
class CalculatePrice(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        product_ids: List[str],
        quantities: Optional[List[int]] = None,
        loyalty_tier: Optional[str] = None,
        shipping_service: Optional[str] = None,
    ) -> str:
        """Calculate subtotal/discount/shipping/total for a list of products.

        This mirrors the legacy SQL-based implementation:
          - Reads product rows from a `products` table.
          - Subtotal = sum(price * quantity) for each product id.
          - Optional loyalty discount: silver 5%, gold 10%, platinum 15%.
          - Shipping: standard 9.99, express 19.99, overnight 39.99.
        """
        if quantities is None:
            quantities = [1] * len(product_ids)

        if len(product_ids) != len(quantities):
            return json.dumps({"error": "product_ids and quantities must have same length"})

        conn = sqlite3.connect(":memory:")
        try:
            build_sqlite_from_data(conn, data)

            placeholders = ",".join(["?"] * len(product_ids)) if product_ids else "NULL"
            query = f"""
                SELECT id, name, price, weight, inventory_count
                FROM products
                WHERE id IN ({placeholders})
            """
            cur = conn.cursor()
            cur.execute(query, product_ids)
            products = {row[0]: row for row in cur.fetchall()}  # id -> row tuple

            subtotal = 0.0
            for pid, qty in zip(product_ids, quantities):
                row = products.get(pid)
                if not row:
                    continue
                price = float(row[2] or 0.0)  # price column
                subtotal += price * int(qty)

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
        finally:
            conn.close()

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
                            "description": "Optional loyalty tier: silver, gold, or platinum.",
                        },
                        "shipping_service": {
                            "type": "string",
                            "description": "Shipping speed: standard, express, or overnight. Defaults to standard.",
                        },
                    },
                    "required": ["product_ids"],
                },
            },
        }
