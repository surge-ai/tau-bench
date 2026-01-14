import json
import hashlib
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool


def _now_iso_from_data(data: Dict[str, Any]) -> str:
    """Get deterministic timestamp from data or use fallback."""
    for k in ("__now", "now", "current_time", "currentTime"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return "1970-01-01T00:00:00Z"


class InitiateRefundProcess(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: str,
        reason: str,
        product_ids: List[str],
        amount: Optional[float] = None,
    ) -> str:
        """Initiate refund process for an order. Validates order/payment and creates refund record."""
        # Validate order exists
        order_table = data.get("order", {})
        if not isinstance(order_table, dict) or order_id not in order_table:
            return json.loads(json.dumps({"error": f"Order {order_id} not found"}))

        order = order_table[order_id]

        # Find payment for this order
        payment_table = data.get("payment", {})
        payment = None
        if isinstance(payment_table, dict):
            for p in payment_table.values():
                if isinstance(p, dict) and p.get("orderId") == order_id:
                    payment = p
                    break

        if not payment:
            return json.loads(json.dumps({"error": f"No payment found for order {order_id}"}))

        payment_id = payment.get("id")
        payment_amount = float(payment.get("amount", 0))

        # Determine refund amount
        if amount is None:
            # Full refund
            refund_amount = payment_amount
        else:
            refund_amount = float(amount)
            if refund_amount > payment_amount:
                return json.loads(json.dumps({
                    "error": f"Refund amount ${refund_amount} exceeds payment amount ${payment_amount}"
                }))

        # Validate products (required)
        if not product_ids:
            return json.loads(json.dumps({"error": "product_ids is required - must specify which products are being refunded"}))

        order_product_ids = [item.get("productId") for item in order.get("lineItems", [])]
        for pid in product_ids:
            if pid not in order_product_ids:
                return json.loads(json.dumps({"error": f"Product {pid} not found in order"}))

        # Generate refund ID
        id_input = f"{payment_id}|{refund_amount}|{reason}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        refund_id = f"refund_{id_hash}"

        # Create refund record
        refund = {
            "id": refund_id,
            "type": "refund",
            "orderId": order_id,
            "paymentId": payment_id,
            "amount": refund_amount,
            "currency": payment.get("currency", "USD"),
            "reason": reason,
            "status": "pending",
            "productIds": product_ids,
            "createdAt": _now_iso_from_data(data),
            "processedAt": None,
        }

        # Store refund
        if "refund" not in data or not isinstance(data["refund"], dict):
            data["refund"] = {}
        data["refund"][refund_id] = refund

        return json.loads(json.dumps({
            "success": True,
            "refund": refund,
            "message": f"Refund {refund_id} initiated for ${refund_amount}",
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "initiate_refund_process",
                "description": "Initiate refund process for an order. Validates order and payment, creates refund record with pending status. **product_ids is REQUIRED** - you must specify which products are being refunded for audit and quality tracking purposes. **CRITICAL: Verify all parameters (order_id, reason, product_ids, amount) are correct before calling. Refund entities cannot be deleted once created.**",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Order ID to refund.",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for refund (e.g., customer_remorse, defective, incompatible).",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Refund amount in dollars. **Must be calculated based on items being refunded** (e.g., if refunding 4 items at $129.99 each, amount should be 519.96). If omitted, full payment amount is refunded. Do not pass 0 or incorrect amounts.",
                        },
                        "product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of product IDs being refunded (REQUIRED). Must specify which products caused the refund for audit trail and quality tracking. Look up product IDs from the order's lineItems.",
                        },
                    },
                    "required": ["order_id", "reason", "product_ids"],
                },
            },
        }
