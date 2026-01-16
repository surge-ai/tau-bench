import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool

# Handle both relative and absolute imports for tests
try:
    from .utils import (
        get_now_iso_from_data,
    )
except ImportError:
    from utils import (
        get_now_iso_from_data,
    )


# Required component categories for a valid build
REQUIRED_BUILD_CATEGORIES = {
    "cpu",
    "motherboard",
    "memory",
    "storage",
    "psu",
    "case",
}


class CreateAndOrderBuild(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        customer_id: str,
        ownerType: str,
        name: str,
        components: Dict[str, Dict[str, Any]],
    ) -> str:
        """
        Create a new build with specified components and create an order for it.

        Args:
            data: The data dictionary
            customer_id: ID of the customer
            ownerType: Owner type ("customer" or "internal")
            name: Name of the build
            components: Dict mapping component types to {"product_id": str, "qty": int (optional)}
                       Example: {"cpu": {"product_id": "novachip-pulse-10600k", "qty": 1}}

        Returns:
            JSON string with success/error information
        """
        # Validate ownerType
        valid_owner_types = ["customer", "internal"]
        if ownerType not in valid_owner_types:
            return json.loads(json.dumps({
                "error": f"Invalid ownerType '{ownerType}'. Must be one of: {', '.join(valid_owner_types)}"
            }))

        # Validate components is a dict
        if not isinstance(components, dict):
            return json.loads(json.dumps({
                "error": "components must be a dictionary"
            }))

        # Validate that products exist and get product data
        product_table = data.get("product")
        if not product_table or not isinstance(product_table, dict):
            return json.loads(json.dumps({
                "error": "Product data not found in system"
            }))

        # Extract and validate component information
        component_ids = []
        line_items = []
        component_categories_provided = set()
        invalid_components = []

        for component_type, component_info in components.items():
            # Validate component_info structure
            if not isinstance(component_info, dict):
                return json.loads(json.dumps({
                    "error": f"Component '{component_type}' must be a dictionary with 'product_id' and optional 'qty'"
                }))

            # Extract product_id
            product_id = component_info.get("product_id")
            if not product_id:
                return json.loads(json.dumps({
                    "error": f"Component '{component_type}' missing required 'product_id' field"
                }))

            # Validate product exists
            product = product_table.get(product_id)
            if not product:
                invalid_components.append(f"{component_type}: {product_id}")
                continue

            # Get product category
            product_category = product.get("category")
            if product_category:
                component_categories_provided.add(product_category)

            # Get quantity (default to 1)
            qty = component_info.get("qty", 1)
            if not isinstance(qty, int) or qty < 1:
                return json.loads(json.dumps({
                    "error": f"Component '{component_type}' has invalid quantity. Must be a positive integer."
                }))

            # Add to component list and line items
            component_ids.append(product_id)
            line_items.append({
                "productId": product_id,
                "qty": qty
            })

        # Check for invalid products
        if invalid_components:
            return json.loads(json.dumps({
                "error": f"Invalid product IDs: {', '.join(invalid_components)}"
            }))

        # Validate that all required categories are present
        missing_categories = REQUIRED_BUILD_CATEGORIES - component_categories_provided
        if missing_categories:
            return json.loads(json.dumps({
                "error": f"Build is missing required component categories: {', '.join(sorted(missing_categories))}",
                "missing_categories": sorted(list(missing_categories)),
                "required_categories": sorted(list(REQUIRED_BUILD_CATEGORIES)),
                "provided_categories": sorted(list(component_categories_provided))
            }))

        # Get current timestamp
        now = get_now_iso_from_data(data)

        # Generate build ID
        if "build" not in data or not isinstance(data.get("build"), dict):
            data["build"] = {}
        build_table = data["build"]

        # Find next available configurator ID for this customer
        customer_build_count = 0
        customer_name_part = customer_id.split("-")[0] if "-" in customer_id else customer_id
        for build_id in build_table.keys():
            if build_id.startswith(f"configurator-{customer_name_part}-"):
                try:
                    num = int(build_id.split("-")[-1])
                    customer_build_count = max(customer_build_count, num + 1)
                except (ValueError, IndexError):
                    pass

        # Create build ID
        build_id = f"configurator-{customer_name_part}-{customer_build_count}"

        # Create new build
        new_build = {
            "ownerType": ownerType,
            "customerId": customer_id,
            "name": name,
            "componentIds": component_ids,
            "createdAt": now,
            "updatedAt": now,
        }

        # Add to build table
        build_table[build_id] = new_build

        # Generate order ID
        if "order" not in data or not isinstance(data.get("order"), dict):
            data["order"] = {}
        order_table = data["order"]

        # Find next available order ID
        order_count = len(order_table)
        # Extract date part from timestamp for order ID (format: ord-YYMMDD-NNN)
        date_part = now.split("T")[0].replace("-", "")[2:]  # Get YYMMDD
        order_id = f"ord-{date_part}-{order_count:03d}"

        # Ensure unique order ID
        while order_id in order_table:
            order_count += 1
            order_id = f"ord-{date_part}-{order_count:03d}"

        # Create new order
        new_order = {
            "customerId": customer_id,
            "buildId": build_id,
            "lineItems": line_items,
            "status": "pending",
            "createdAt": now,
            "updatedAt": now,
        }

        # Add to order table
        order_table[order_id] = new_order

        return json.loads(json.dumps({
            "success": True,
            "build_id": build_id,
            "build": new_build,
            "order_id": order_id,
            "order": new_order,
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_and_order_build",
                "description": f"Create a new PC build configuration with specified components and automatically create an order for it. All required component categories must be provided: {', '.join(sorted(REQUIRED_BUILD_CATEGORIES))}. Each component must exist in the product catalog.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "ID of the customer who owns this build.",
                        },
                        "ownerType": {
                            "type": "string",
                            "description": "Owner type of the build.",
                            "enum": ["customer", "internal"],
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the build configuration.",
                        },
                        "components": {
                            "type": "object",
                            "description": f"Dictionary mapping component types to their details. Each component must have 'product_id' (required) and 'qty' (optional, defaults to 1). Required categories: {', '.join(sorted(REQUIRED_BUILD_CATEGORIES))}. Example: {{'cpu': {{'product_id': 'novachip-pulse-10600k', 'qty': 1}}, 'motherboard': {{'product_id': 'cryonix-z790-apex'}}}}",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "product_id": {
                                        "type": "string",
                                        "description": "Product ID for this component."
                                    },
                                    "qty": {
                                        "type": "integer",
                                        "description": "Quantity of this component (default: 1)."
                                    }
                                },
                                "required": ["product_id"]
                            }
                        },
                    },
                    "required": ["customer_id", "ownerType", "name", "components"],
                },
            },
        }
