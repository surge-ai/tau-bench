import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class UpdatePaymentStatus(Tool):
    @staticmethod
    def invoke(data: Dict[str,Any], **kwargs)->str:
        payment_id = kwargs.get("payment_id")
        new_status = kwargs.get("status")
        updated = False

        payment_table = data.get("payment")
        if isinstance(payment_table, dict) and payment_id in payment_table:
            payment_table[payment_id]["status"] = new_status
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
                            "enum": ["pending", "authorized", "captured", "failed", "refunded", "disputed", "voided", "completed"],
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
