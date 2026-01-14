import json
import hashlib
from typing import Any, Dict, Optional

from tau_bench.envs.tool import Tool

from .data_utils import get_entity_by_id, validate_enum


# Valid enum values
VALID_STATUSES = ["pending_review", "accepted", "denied"]
VALID_REASONS = ["defect", "wear_and_tear", "malfunction"]
VALID_DENIAL_REASONS = [
    "product_misuse",
    "uncovered_damage",
    "out_of_warranty",
    "unauthorized_modification",
    "insufficient_evidence",
]

# Product categories that cannot have warranty claims (must claim individual components)
BUILD_PRODUCT_CATEGORIES = ["prebuilt", "workstation"]


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


class CreateWarrantyClaim(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        product_id: str,
        order_id: str,
        customer_id: str,
        reason: str,
        status: Optional[str] = "pending_review",
        denial_reason: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new warranty claim for a product.

        Persisted fields:
          - id: warranty_claim_<hash>
          - productId
          - orderId
          - customerId
          - reason
          - status
          - denialReason (optional, typically set when status is "denied")
          - notes (optional)
          - createdAt
          - updatedAt
        """
        # Validate enum parameters
        validate_enum(status, VALID_STATUSES, "status")
        validate_enum(reason, VALID_REASONS, "reason")
        validate_enum(denial_reason, VALID_DENIAL_REASONS, "denial_reason")

        # Validate referenced entities exist
        product = get_entity_by_id(data, "product", product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Check if product is a build category (prebuilt/workstation)
        product_category = product.get("category", "")
        if product_category in BUILD_PRODUCT_CATEGORIES:
            raise ValueError(
                f"Cannot create warranty claim for {product_category} products. "
                f"Warranty claims must be filed for individual components within the build. "
                f"Please identify the specific component that is defective and create a claim for that part."
            )

        if not get_entity_by_id(data, "order", order_id):
            raise ValueError(f"Order {order_id} not found")
        if not get_entity_by_id(data, "customer", customer_id):
            raise ValueError(f"Customer {customer_id} not found")

        # Generate deterministic ID based on input parameters
        id_input = f"{product_id}|{order_id}|{customer_id}|{reason}|{status or 'pending_review'}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        claim_id = f"warranty_claim_{id_hash}"

        now = _now_iso_from_data(data)
        row: Dict[str, Any] = {
            "id": claim_id,
            "productId": product_id,
            "orderId": order_id,
            "customerId": customer_id,
            "reason": reason,
            "status": status or "pending_review",
            "denialReason": denial_reason,
            "notes": notes,
            "createdAt": now,
            "updatedAt": now,
        }

        # Use dictionary format keyed by ID
        if "warranty_claim" not in data or not isinstance(data["warranty_claim"], dict):
            data["warranty_claim"] = {}
        data["warranty_claim"][claim_id] = row

        return json.loads(json.dumps(row))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "createWarrantyClaim",
                "description": "Create a new warranty claim for a product. Use this when a customer reports a product issue that may be covered under warranty.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "The ID of the product being claimed under warranty.",
                        },
                        "order_id": {
                            "type": "string",
                            "description": "The ID of the order containing the product.",
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "The ID of the customer making the claim.",
                        },
                        "reason": {
                            "type": "string",
                            "enum": VALID_REASONS,
                            "description": "The reason for the warranty claim.",
                        },
                        "status": {
                            "type": "string",
                            "enum": VALID_STATUSES,
                            "description": "The status of the warranty claim (default: pending_review).",
                        },
                        "denial_reason": {
                            "type": "string",
                            "enum": VALID_DENIAL_REASONS,
                            "description": "The reason for denial (only applicable when status is 'denied').",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional notes about the warranty claim.",
                        },
                    },
                    "required": ["product_id", "order_id", "customer_id", "reason"],
                },
            },
        }
