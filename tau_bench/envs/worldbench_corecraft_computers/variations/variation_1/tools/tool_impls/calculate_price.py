import json
from typing import Annotated, Dict, List, Optional

from pydantic import Field
from utils import get_db_conn


def calculatePrice(
    product_ids: Annotated[List[str], Field(description="The product_ids parameter")],
    quantities: Annotated[
        Optional[List[float]],
        Field(description="The quantities parameter")
    ] = None,
    loyalty_tier: Annotated[Optional[str], Field(description="The loyalty_tier parameter")] = None,
    shipping_service: Annotated[Optional[str], Field(description="The shipping_service parameter")] = None,
) -> Dict[str, float]:
    """Calculate total price with discounts"""
    # Default quantities to 1 for each product
    if not quantities:
        quantities = [1.0] * len(product_ids)

    # Ensure quantities match product_ids length
    if len(quantities) < len(product_ids):
        quantities.extend([1.0] * (len(product_ids) - len(quantities)))

    conn = get_db_conn()

    try:
        cursor = conn.cursor()

        # Get products
        placeholders = ",".join("?" * len(product_ids))
        cursor.execute(f"SELECT * FROM Product WHERE id IN ({placeholders})", product_ids)
        rows = cursor.fetchall()

        # Build product map
        product_map = {}
        for row in rows:
            product = dict(row)
            product_map[product["id"]] = product

        # Calculate subtotal
        subtotal = 0.0
        for idx, product_id in enumerate(product_ids):
            product = product_map.get(product_id)
            if product and product.get("price"):
                price = float(product["price"])
                quantity = float(quantities[idx])
                subtotal += price * quantity

        # Apply loyalty discount
        discount = 0.0
        if loyalty_tier:
            discounts = {
                "silver": 0.05,
                "gold": 0.1,
                "platinum": 0.15,
            }
            discount = subtotal * discounts.get(loyalty_tier.lower(), 0)

        # Shipping
        shipping_rates = {
            "standard": 9.99,
            "express": 19.99,
            "overnight": 39.99,
        }
        shipping = shipping_rates.get((shipping_service or "standard").lower(), 9.99)

        after_discount = subtotal - discount
        total = after_discount + shipping

        return {
            "subtotal": round(subtotal * 100) / 100,
            "discount": round(discount * 100) / 100,
            "shipping": shipping,
            "total": round(total * 100) / 100,
        }
    finally:
        conn.close()
