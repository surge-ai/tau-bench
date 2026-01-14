import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

from .data_utils import validate_enum


class _NotProvided:
    pass


_NOT_PROVIDED = _NotProvided()


class UpdatePaymentStatus(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        payment_id: str,
        status: str,
        failure_reason: str | None | _NotProvided = _NOT_PROVIDED,
    ) -> str:
        # Validate enum parameters
        validate_enum(status, ["pending", "captured", "failed", "refunded", "partially_refunded"], "status")

        payment_table = data.get("payment")
        if not isinstance(payment_table, dict):
            raise ValueError("Payment table not found in data")
        if payment_id not in payment_table:
            raise ValueError(f"Payment {payment_id} not found")

        payment_table[payment_id]["status"] = status
        if failure_reason is not _NOT_PROVIDED:
            payment_table[payment_id]["failure_reason"] = failure_reason
        return json.loads(json.dumps(payment_table[payment_id]))

    @staticmethod
    def get_info()->Dict[str,Any]:
        return {
            "type":"function",
            "function":{
                "name":"updatePaymentStatus",
                "description":"Update the status of a payment. Returns whether the update was successful.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "payment_id": {
                            "type": "string",
                            "description": "The payment ID to update"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "captured", "failed", "refunded", "partially_refunded"],
                            "description": "The new status to set for the payment"
                        },
                        "failure_reason": {
                            "type": ["string", "null"],
                            "description": "Reason for payment failure (used when status is 'failed'), or null to clear"
                        }
                    },
                    "required":["payment_id", "status"]
                }
            }
        }
