import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import validate_enum


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




def _find_payment(data: Dict[str, Any], payment_id: str) -> Optional[Dict[str, Any]]:
    payment_table = data.get("payment")
    if isinstance(payment_table, dict) and payment_id in payment_table:
        return payment_table[payment_id]
    return None


class CreateRefund(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        payment_id: str,
        amount: float,
        reason: str,
        status: Optional[str] = "pending",
        lines: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Create a refund for an existing payment.

        Persisted fields (mirrors legacy SQL columns):
          - id: refund_<uuid4hex>
          - type: "refund"
          - paymentId
          - amount
          - reason
          - status
          - lines (list of dicts)
          - createdAt
          - processedAt (None)
        """
        # Validate enum parameters
        validate_enum(reason, ["customer_remorse", "defective", "incompatible", "shipping_issue", "other"], "reason")
        validate_enum(status, ["pending", "approved", "denied", "processed", "failed"], "status")

        if not _find_payment(data, payment_id):
            raise ValueError(f"Payment {payment_id} not found")

        # Generate deterministic ID based on input parameters
        id_input = f"{payment_id}|{amount}|{reason}|{status or 'pending'}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        refund_id = f"refund_{id_hash}"
        row: Dict[str, Any] = {
            "id": refund_id,
            "type": "refund",
            "paymentId": payment_id,
            "amount": float(amount),
            "reason": reason,
            "status": status or "pending",
            "lines": lines or [],
            "createdAt": _now_iso_from_data(data),
            "processedAt": None,
        }

        # Use dictionary format keyed by ID
        if "refund" not in data or not isinstance(data["refund"], dict):
            data["refund"] = {}
        data["refund"][refund_id] = row

        return json.loads(json.dumps(row))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_refund",
                "description": "Create a refund record associated with a payment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "payment_id": {"type": "string", "description": "Payment ID to refund."},
                        "amount": {"type": "number", "description": "Refund amount."},
                        "reason": {
                            "type": "string",
                            "enum": ["customer_remorse", "defective", "incompatible", "shipping_issue", "other"],
                            "description": "Reason for refund.",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "approved", "denied", "processed", "failed"],
                            "description": "Refund status (default: pending).",
                        },
                        "lines": {
                            "type": "array",
                            "description": "Line items for the refund. Each line should be an object with keys: sku (product SKU), qty (quantity being refunded), and amount (price of an individual unit of that line item).",
                            "items": {"type": "object"},
                        },
                    },
                    "required": ["payment_id", "amount", "reason"],
                },
            },
        }
