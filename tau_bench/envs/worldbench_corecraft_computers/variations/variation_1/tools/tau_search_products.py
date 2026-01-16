import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_entity_json_fields,
    matches_text_search,
    apply_limit,
    validate_enum,
)

PRODUCT_CATEGORIES = ["cpu", "motherboard", "gpu", "memory", "storage", "psu", "case", "cooling", "prebuilt", "workstation", "monitor", "keyboard", "mouse", "headset", "networking", "cable", "accessory", "bundle"]


def _get_inventory_in_stock(entity: Dict[str, Any]) -> Optional[int]:
    """Get inStock value from inventory field (handles JSON string or dict)."""
    inventory = entity.get("inventory")
    if inventory is None:
        return None
    if isinstance(inventory, str):
        try:
            inventory = json.loads(inventory)
        except (json.JSONDecodeError, TypeError):
            return None
    if isinstance(inventory, dict):
        return inventory.get("inStock")
    return None


class SearchProducts(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        price: Optional[float] = None,
        inStockOnly: Optional[bool] = None,
        minStock: Optional[float] = None,
        maxStock: Optional[float] = None,
        text: Optional[str] = None,
        limit: Optional[float] = None,
        product_id: Optional[str] = None,
    ) -> str:
        validate_enum(category, PRODUCT_CATEGORIES, "category")

        results: List[Dict[str, Any]] = []

        for row in iter_entities(data, "product"):
            # Exact product_id match
            if product_id and row.get("id") != product_id:
                continue
            # Exact category match
            if category and row.get("category") != category:
                continue
            # Exact brand match
            if brand and row.get("brand") != brand:
                continue
            # Price filtering
            row_price = row.get("price")
            if row_price is not None:
                if min_price is not None and row_price < min_price:
                    continue
                if max_price is not None and row_price > max_price:
                    continue
                if price is not None and row_price != price:
                    continue

            # Stock filtering
            in_stock = _get_inventory_in_stock(row)
            if inStockOnly and (in_stock is None or in_stock <= 0):
                continue
            if minStock is not None and (in_stock is None or in_stock < minStock):
                continue
            if maxStock is not None and (in_stock is None or in_stock > maxStock):
                continue

            # Text search across name, brand, and SKU
            if text and not matches_text_search(row, ["name", "brand", "sku"], text):
                continue

            # Parse JSON fields
            result_row = parse_entity_json_fields(row, ["inventory", "specs"])
            results.append(result_row)

        # Sort by name ASC, then id ASC
        results.sort(key=lambda p: (p.get("name", ""), p.get("id", "")))

        # Apply limit
        results = apply_limit(results, limit)

        return json.loads(json.dumps(results, default=str))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchProducts",
                "description": "Search for products with various filters. Returns an array of product records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["cpu", "motherboard", "gpu", "memory", "storage", "psu", "case", "cooling", "prebuilt", "workstation", "monitor", "keyboard", "mouse", "headset", "networking", "cable", "accessory", "bundle"],
                            "description": "Product category to filter by"
                        },
                        "brand": {
                            "type": "string",
                            "description": "Product brand name to filter by"
                        },
                        "min_price": {
                            "type": "number",
                            "description": "Minimum price filter"
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price filter"
                        },
                        "price": {
                            "type": "number",
                            "description": "Exact price filter"
                        },
                        "inStockOnly": {
                            "type": "boolean",
                            "description": "Set to True to only return products with inventory > 0"
                        },
                        "minStock": {
                            "type": "number",
                            "description": "Minimum stock level filter"
                        },
                        "maxStock": {
                            "type": "number",
                            "description": "Maximum stock level filter"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text search across name, brand, and SKU"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default 50, max 200)"
                        },
                        "product_id": {
                            "type": "string",
                            "description": "Exact product ID filter"
                        }
                    },
                    "required": []
                }
            }
        }
