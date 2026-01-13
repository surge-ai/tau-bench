import json
import hashlib
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool

from .data_utils import get_entity_by_id


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


class CreateBuild(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        name: str,
        customer_id: str,
        product_ids: List[str],
    ) -> Dict[str, Any]:
        """Create a new PC build configuration for a customer.

        Persisted fields:
          - id: build_<hash>
          - name
          - customerId
          - productIds (list of product IDs, sorted)
          - createdAt
          - updatedAt
        """
        if not get_entity_by_id(data, "customer", customer_id):
            raise ValueError(f"Customer {customer_id} not found")

        # Validate all product IDs exist
        for product_id in product_ids:
            if not get_entity_by_id(data, "product", product_id):
                raise ValueError(f"Product {product_id} not found")

        # Sort product IDs for deterministic ordering
        sorted_product_ids = sorted(product_ids)

        # Generate deterministic ID based on input parameters
        id_input = f"{name}|{customer_id}|{'|'.join(sorted_product_ids)}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        build_id = f"build_{id_hash}"

        now = _now_iso_from_data(data)
        row: Dict[str, Any] = {
            "id": build_id,
            "name": name,
            "customerId": customer_id,
            "productIds": sorted_product_ids,
            "createdAt": now,
            "updatedAt": now,
        }

        # Use dictionary format keyed by ID
        if "build" not in data or not isinstance(data["build"], dict):
            data["build"] = {}
        data["build"][build_id] = row

        return json.loads(json.dumps(row))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "createBuild",
                "description": "Create a new PC build configuration for a customer. A build is a saved collection of compatible PC components.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name for the build configuration (e.g., 'Gaming PC', 'Workstation Build').",
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID who owns this build.",
                        },
                        "product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of product IDs to include in the build.",
                        },
                    },
                    "required": ["name", "customer_id", "product_ids"],
                },
            },
        }
