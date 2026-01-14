import json
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


class UpdateBuild(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        build_id: str,
        name: Optional[str] = None,
        add_product_ids: Optional[List[str]] = None,
        remove_product_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update an existing PC build configuration.

        Allows updating the build name and modifying the product list
        by adding or removing products.

        Args:
            data: The data dictionary
            build_id: The ID of the build to update
            name: Optional new name for the build
            add_product_ids: Optional list of product IDs to add to the build
            remove_product_ids: Optional list of product IDs to remove from the build

        Returns:
            The updated build as a dictionary
        """
        build_table = data.get("build")
        if not isinstance(build_table, dict):
            raise ValueError("Build table not found in data")
        if build_id not in build_table:
            raise ValueError(f"Build {build_id} not found")

        build = build_table[build_id]

        # Validate products to add exist and collect all not found
        if add_product_ids:
            not_found = [pid for pid in add_product_ids if not get_entity_by_id(data, "product", pid)]
            if not_found:
                raise ValueError(f"Products not found: {', '.join(not_found)}")

        # Update product list (use list to allow duplicates like multiple RAM sticks)
        current_products = list(build.get("productIds", []))

        # Validate products to remove exist in the build
        if remove_product_ids:
            not_in_build = [pid for pid in remove_product_ids if pid not in current_products]
            if not_in_build:
                raise ValueError(f"Products not in build: {', '.join(not_in_build)}")

        # Update name if provided
        if name is not None:
            build["name"] = name

        if remove_product_ids:
            for product_id in remove_product_ids:
                current_products.remove(product_id)

        if add_product_ids:
            current_products.extend(add_product_ids)

        # Sort product IDs for deterministic ordering
        build["productIds"] = sorted(current_products)

        # Update timestamp
        build["updatedAt"] = _now_iso_from_data(data)

        return json.loads(json.dumps(build))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "updateBuild",
                "description": "Update an existing PC build configuration. Allows changing the build name and modifying the product list by adding or removing products.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "build_id": {
                            "type": "string",
                            "description": "The ID of the build to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "Optional new name for the build configuration.",
                        },
                        "add_product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of product IDs to add to the build.",
                        },
                        "remove_product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of product IDs to remove from the build.",
                        },
                    },
                    "required": ["build_id"],
                },
            },
        }
