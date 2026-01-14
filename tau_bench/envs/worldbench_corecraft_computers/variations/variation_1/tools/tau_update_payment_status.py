import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

_NOT_PROVIDED = object()


class UpdatePaymentStatus(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        payment_id: str,
        status: str,
        failure_reason: Any = _NOT_PROVIDED,
    ) -> str:
        updated = False

        payment_table = data.get("payment")
        if isinstance(payment_table, dict) and payment_id in payment_table:
            payment_table[payment_id]["status"] = status
            if failure_reason is not _NOT_PROVIDED:
                payment_table[payment_id]["failure_reason"] = failure_reason
            updated = True

        return json.dumps({"updated": updated})

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
                            "type": "string",
                            "description": "Optional reason for payment failure (used when status is 'failed')"
                        }
                    },
                    "required":["payment_id", "status"]
                }
            }
        }
