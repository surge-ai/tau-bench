import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from tau_bench.envs.tool import Tool


class GetShippingEstimates(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        destination_zip: Optional[str] = None,
        shipping_method: Optional[str] = "standard",
    ) -> str:
        """Get shipping cost and delivery time estimates for products."""

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

        # Add destination surcharge (simplified - based on zip code prefix)
        destination_surcharge = 0.0
        if destination_zip:
            # Simplified: if zip starts with 9 (West Coast), add surcharge
            if destination_zip.startswith("9"):
                destination_surcharge = 5.00

        total_cost = base_cost + destination_surcharge

        # Calculate estimated delivery date
        # Add 1 day for processing
        if method != "overnight":
            processing_days=0
            total_days = base_days + 1
        else:
            processing_days=1
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
            "cost_breakdown": {
                "base_rate": base_cost,
                "destination_surcharge": round(destination_surcharge, 2),
                "total_cost": round(total_cost, 2),
            },
            "timing": {
                "processing_days": processing_days,
                "transit_days": base_days,
                "total_days": total_days,
                "estimated_ship_date": estimated_ship.strftime("%Y-%m-%d"),
                "estimated_delivery_date": estimated_delivery.strftime("%Y-%m-%d"),
            },
            "destination_zip": destination_zip,
        }

        return json.loads(json.dumps(result))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_shipping_estimates",
                "description": "Get shipping cost and delivery time estimates for an order, including destination surcharges.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destination_zip": {
                            "type": "string",
                            "description": "Destination ZIP code for delivery (affects cost).",
                        },
                        "shipping_method": {
                            "type": "string",
                            "description": "Shipping method: standard, express, overnight, two_day, or free (default: standard).",
                        },
                    },
                    "required": ["shipping_method", "destination_zip"],
                },
            },
        }
