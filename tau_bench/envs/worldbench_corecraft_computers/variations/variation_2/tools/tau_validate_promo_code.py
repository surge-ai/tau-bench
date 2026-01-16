import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

# Define active promo codes with their details
ACTIVE_PROMO_CODES = {
    "WELCOME10": {
        "code": "WELCOME10",
        "description": "10% off for new customers",
        "discountType": "percentage",
        "discountValue": 10.0,
        "minimumPurchase": 0.0,
        "maxDiscount": None,
    },
    "SAVE25": {
        "code": "SAVE25",
        "description": "$25 off orders over $200",
        "discountType": "fixed",
        "discountValue": 25.0,
        "minimumPurchase": 200.0,
        "maxDiscount": None,
    },
    "BULK20": {
        "code": "BULK20",
        "description": "20% off orders over $500",
        "discountType": "percentage",
        "discountValue": 20.0,
        "minimumPurchase": 500.0,
        "maxDiscount": 100.0,
    },
    "FREESHIP": {
        "code": "FREESHIP",
        "description": "Free shipping on all orders",
        "discountType": "free_shipping",
        "discountValue": 0.0,
        "minimumPurchase": 0.0,
        "maxDiscount": None,
    },
    "VIP15": {
        "code": "VIP15",
        "description": "15% off for VIP members (gold and platinum loyalty tiers)",
        "discountType": "percentage",
        "discountValue": 15.0,
        "minimumPurchase": 0.0,
        "maxDiscount": 150.0,
    },
}


class ValidatePromoCode(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        promo_code: str,
    ) -> str:
        """Validate a promo code and return its details if valid."""
        # Normalize promo code to uppercase for case-insensitive matching
        promo_code_upper = promo_code.strip().upper()

        # Check if the promo code exists
        if promo_code_upper not in ACTIVE_PROMO_CODES:
            # Provide helpful suggestions for similar codes
            all_codes = sorted(ACTIVE_PROMO_CODES.keys())
            return json.loads(json.dumps({
                "valid": False,
                "promo_code": promo_code,
                "error": f"Promo code '{promo_code}' is not valid or has expired",
                "active_promo_codes": all_codes,
                "message": "Please check the promo code and try again, or use one of the active promo codes listed.",
            }))

        # Promo code is valid
        promo_details = ACTIVE_PROMO_CODES[promo_code_upper]

        return json.loads(json.dumps({
            "valid": True,
            "promo_code": promo_code_upper,
            "description": promo_details["description"],
            "discount_type": promo_details["discountType"],
            "discount_value": promo_details["discountValue"],
            "minimum_purchase": promo_details["minimumPurchase"],
            "max_discount": promo_details["maxDiscount"],
            "message": f"Promo code '{promo_code_upper}' is valid: {promo_details['description']}",
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "validate_promo_code",
                "description": "Validate a promotional code and retrieve its discount details. Returns information about the discount type (percentage, fixed amount, or free shipping), discount value, and any conditions like minimum purchase requirements. Case-insensitive.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "promo_code": {
                            "type": "string",
                            "description": "The promotional code to validate (e.g., 'WELCOME10', 'SAVE25'). Case-insensitive.",
                        },
                    },
                    "required": ["promo_code"],
                },
            },
        }
