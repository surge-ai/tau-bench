import json
import re
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import get_entity_data_key
except ImportError:
    from utils import get_entity_data_key


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalize phone number by removing all non-digit characters.
    Also strips leading "1" for US/Canada country code if present.
    Returns None if phone is None or empty.
    """
    if not phone:
        return None
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    if not digits:
        return None
    # Strip leading "1" if it's 11 digits (US/Canada country code)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    return digits


class VerifyCustomer(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        customer_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        zip_code: Optional[str] = None,
    ) -> str:
        """
        Verify customer identity by checking provided information.

        Returns validated=True if at least 2 of 3 identifiers match.
        Returns validated=False if ANY provided information is incorrect.
        Returns error if fewer than 2 identifiers are provided.
        """
        # Count how many identifiers were provided
        provided_identifiers = []
        if email is not None:
            provided_identifiers.append("email")
        if phone is not None:
            provided_identifiers.append("phone")
        if zip_code is not None:
            provided_identifiers.append("zip_code")

        # Require at least 2 identifiers
        if len(provided_identifiers) < 2:
            return json.loads(json.dumps({
                "error": "At least 2 of the following must be provided: email, phone, zip_code",
                "provided_identifiers": provided_identifiers,
                "required_count": 2,
                "actual_count": len(provided_identifiers),
            }))

        # Get customer data
        data_key = get_entity_data_key("customer")
        customer_table = data.get(data_key, {})

        if not isinstance(customer_table, dict) or customer_id not in customer_table:
            return json.loads(json.dumps({
                "error": f"Customer {customer_id} not found",
                "customer_id": customer_id,
            }))

        customer = customer_table[customer_id]

        # Track matches and mismatches
        matches = []
        mismatches = []

        # Check email (case-insensitive)
        if email is not None:
            customer_email = customer.get("email", "").lower()
            provided_email = email.lower()
            if customer_email == provided_email:
                matches.append("email")
            else:
                mismatches.append({
                    "field": "email",
                    "provided": email,
                    "message": "Email does not match customer record"
                })

        # Check phone (normalized - digits only)
        if phone is not None:
            customer_phone = normalize_phone(customer.get("phone"))
            provided_phone = normalize_phone(phone)

            if customer_phone and provided_phone and customer_phone == provided_phone:
                matches.append("phone")
            else:
                mismatches.append({
                    "field": "phone",
                    "provided": phone,
                    "message": "Phone number does not match customer record"
                })

        # Check zip code (check all customer addresses)
        if zip_code is not None:
            customer_addresses = customer.get("addresses", [])
            zip_match = False

            if isinstance(customer_addresses, list):
                for address in customer_addresses:
                    if isinstance(address, dict):
                        # Normalize zip codes (remove spaces, compare case-insensitive)
                        address_zip = address.get("postalCode", "").replace(" ", "").upper()
                        provided_zip = zip_code.replace(" ", "").upper()
                        if address_zip == provided_zip:
                            zip_match = True
                            break

            if zip_match:
                matches.append("zip_code")
            else:
                mismatches.append({
                    "field": "zip_code",
                    "provided": zip_code,
                    "message": "Zip code does not match any customer address"
                })

        # Determine validation result
        # If ANY provided information is incorrect, return validated=False
        if len(mismatches) > 0:
            return json.loads(json.dumps({
                "validated": False,
                "customer_id": customer_id,
                "matches": matches,
                "mismatches": mismatches,
                "match_count": len(matches),
                "mismatch_count": len(mismatches),
                "message": "Validation failed: one or more provided identifiers do not match customer record",
            }))

        # All provided information is correct and we have at least 2 matches
        return json.loads(json.dumps({
            "validated": True,
            "customer_id": customer_id,
            "customer_name": customer.get("name"),
            "matches": matches,
            "match_count": len(matches),
            "message": f"Customer identity verified successfully with {len(matches)} matching identifiers",
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "verify_customer",
                "description": "Verify customer identity by checking provided information against customer records. **Requires at least 2 of: email, phone, zip_code.** Returns validated=True if at least 2 identifiers match. Returns validated=False if ANY provided information is incorrect. Phone numbers can be in various formats: (XXX) XXX-XXXX, XXX-XXX-XXXX, +1-XXX-XXX-XXXX. Zip codes are checked against all customer addresses.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer ID to verify",
                        },
                        "email": {
                            "type": "string",
                            "description": "Customer's email address (optional, but at least 2 of email/phone/zip_code required)",
                        },
                        "phone": {
                            "type": "string",
                            "description": "Customer's phone number in any format: (XXX) XXX-XXXX, XXX-XXX-XXXX, or +1-XXX-XXX-XXXX (optional, but at least 2 of email/phone/zip_code required)",
                        },
                        "zip_code": {
                            "type": "string",
                            "description": "Customer's zip/postal code from any of their addresses (optional, but at least 2 of email/phone/zip_code required)",
                        },
                    },
                    "required": ["customer_id"],
                },
            },
        }
