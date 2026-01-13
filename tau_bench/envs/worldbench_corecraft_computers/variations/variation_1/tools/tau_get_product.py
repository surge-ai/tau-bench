import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

from .data_utils import (
    get_entity_by_id,
    parse_entity_json_fields,
)


class GetProduct(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], product_id: str = None, **kwargs) -> str:
        # Handle product_id passed via kwargs
        if product_id is None:
            product_id = kwargs.get("product_id")

        if not product_id:
            raise ValueError("product_id is required")

        product = get_entity_by_id(data, "product", product_id)

        if not product:
            raise ValueError(f"Product not found: {product_id}")

        # Parse JSON fields
        result = parse_entity_json_fields(product, ["inventory", "specs"])

        return json.dumps(result, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "getProduct",
                "description": "Get detailed information about a product by its ID. Returns the full product record including category, SKU, name, brand, price, inventory, specs, and warranty information. Raises an error if the product is not found.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "The product ID to retrieve"
                        }
                    },
                    "required": ["product_id"],
                },
            },
        }
