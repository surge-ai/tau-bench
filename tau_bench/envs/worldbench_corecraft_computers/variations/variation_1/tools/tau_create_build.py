import json
import hashlib
from typing import Any, Dict, List, Optional

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
        product_ids: List[str],
        owner_type: str = "customer",
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new PC build configuration.

        Persisted fields:
          - id: build_<hash>
          - name
          - ownerType
          - customerId (optional, required if ownerType is "customer")
          - productIds (list of product IDs, sorted)
          - createdAt
          - updatedAt
        """
        # Validate owner_type
        if owner_type not in ["customer", "internal"]:
            raise ValueError(f"Invalid owner_type: {owner_type}. Must be 'customer' or 'internal'")

        # Validate customer_id is provided when owner_type is "customer"
        if owner_type == "customer" and not customer_id:
            raise ValueError("customer_id is required when owner_type is 'customer'")

        # Validate customer exists if customer_id is provided
        if customer_id and not get_entity_by_id(data, "customer", customer_id):
            raise ValueError(f"Customer {customer_id} not found")

        # Validate all product IDs exist and collect all not found
        not_found = [pid for pid in product_ids if not get_entity_by_id(data, "product", pid)]
        if not_found:
            raise ValueError(f"Products not found: {', '.join(not_found)}")

        # Sort product IDs for deterministic ordering
        sorted_product_ids = sorted(product_ids)

        # Generate deterministic ID based on input parameters
        id_input = f"{name}|{owner_type}|{customer_id or ''}|{'|'.join(sorted_product_ids)}"
        id_hash = hashlib.sha256(id_input.encode()).hexdigest()[:12]
        build_id = f"build_{id_hash}"

        now = _now_iso_from_data(data)
        row: Dict[str, Any] = {
            "id": build_id,
            "name": name,
            "ownerType": owner_type,
            "productIds": sorted_product_ids,
            "createdAt": now,
            "updatedAt": now,
        }

        # Add customerId only if provided
        if customer_id:
            row["customerId"] = customer_id

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
                "description": "Create a new PC build configuration. A build is a saved collection of compatible PC components that can be owned by a customer or used internally.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name for the build configuration (e.g., 'Gaming PC', 'Workstation Build').",
                        },
                        "product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of product IDs to include in the build.",
                        },
                        "owner_type": {
                            "type": "string",
                            "enum": ["customer", "internal"],
                            "description": "Owner type for the build. 'customer' means owned by a specific customer, 'internal' means owned by the company (default: customer).",
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID who owns this build. Required when owner_type is 'customer', not used when owner_type is 'internal'.",
                        },
                    },
                    "required": ["name", "product_ids"],
                },
            },
        }
