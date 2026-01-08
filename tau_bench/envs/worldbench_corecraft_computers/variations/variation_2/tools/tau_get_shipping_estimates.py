import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from tau_bench.envs.tool import Tool


class GetShippingEstimates(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        product_ids: List[str],
        destination_zip: Optional[str] = None,
        shipping_method: Optional[str] = "standard",
    ) -> str:
        """Get shipping cost and delivery time estimates for products."""
        product_table = data.get("product", {})
        if not isinstance(product_table, dict):
            return json.dumps({"error": "Product data not available"})

        # Calculate total weight
        total_weight = 0.0
        products = []

        for pid in product_ids:
            product = product_table.get(pid)
            if not product:
                return json.dumps({"error": f"Product {pid} not found"})

            weight = float(product.get("weight", 0))
            total_weight += weight
            products.append({
                "product_id": pid,
                "name": product.get("name"),
                "weight": weight,
            })

        # Base shipping rates by method
        base_rates = {
            "standard": {"cost": 9.99, "days": 7},
            "express": {"cost": 19.99, "days": 3},
            "overnight": {"cost": 39.99, "days": 1},
            "two_day": {"cost": 29.99, "days": 2},
            "free": {"cost": 0.00, "days": 10},
        }

        method = shipping_method.lower()
        if method not in base_rates:
            method = "standard"

        base_cost = base_rates[method]["cost"]
        base_days = base_rates[method]["days"]

        # Add weight surcharge for heavy items
        weight_surcharge = 0.0
        if total_weight > 10:
            weight_surcharge = (total_weight - 10) * 0.50

        # Add destination surcharge (simplified - based on zip code prefix)
        destination_surcharge = 0.0
        if destination_zip:
            # Simplified: if zip starts with 9 (West Coast), add surcharge
            if destination_zip.startswith("9"):
                destination_surcharge = 5.00

        total_cost = base_cost + weight_surcharge + destination_surcharge

        # Calculate estimated delivery date
        # Add 1 day for processing
        total_days = base_days + 1

        # Get current date (use data timestamp if available for determinism)
        current_date = datetime.now()
        for k in ("__now", "now", "current_time"):
            if k in data and isinstance(data[k], str):
                try:
                    current_date = datetime.fromisoformat(data[k].replace("Z", "+00:00"))
                    break
                except:
                    pass

        estimated_delivery = current_date + timedelta(days=total_days)
        estimated_ship = current_date + timedelta(days=1)

        result = {
            "shipping_method": method,
            "products": products,
            "weight": {
                "total_weight_lbs": round(total_weight, 2),
                "is_oversized": total_weight > 50,
            },
            "cost_breakdown": {
                "base_rate": base_cost,
                "weight_surcharge": round(weight_surcharge, 2),
                "destination_surcharge": round(destination_surcharge, 2),
                "total_cost": round(total_cost, 2),
            },
            "timing": {
                "processing_days": 1,
                "transit_days": base_days,
                "total_days": total_days,
                "estimated_ship_date": estimated_ship.strftime("%Y-%m-%d"),
                "estimated_delivery_date": estimated_delivery.strftime("%Y-%m-%d"),
            },
            "destination_zip": destination_zip,
        }

        return json.dumps(result)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_shipping_estimates",
                "description": "Get shipping cost and delivery time estimates for products, including weight and destination surcharges.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of product IDs to estimate shipping for.",
                        },
                        "destination_zip": {
                            "type": "string",
                            "description": "Destination ZIP code for delivery (affects cost).",
                        },
                        "shipping_method": {
                            "type": "string",
                            "description": "Shipping method: standard, express, overnight, two_day, or free (default: standard).",
                        },
                    },
                    "required": ["product_ids"],
                },
            },
        }
