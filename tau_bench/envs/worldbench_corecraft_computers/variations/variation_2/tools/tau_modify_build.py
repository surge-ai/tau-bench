import json
from typing import Any, Dict, List

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


# Categories that can have multiple instances
MULTI_INSTANCE_CATEGORIES = {"memory", "storage"}


class ModifyBuild(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        build_id: str,
        product_id: str,
        action: str,
    ) -> str:
        """
        Modify a build by adding, removing, or swapping a component.

        Args:
            data: The data dictionary
            build_id: ID of the build to modify
            product_id: Product ID to add, remove, or swap
            action: Action to perform ("add", "remove", "swap")

        Returns:
            JSON string with success/error information
        """
        # Validate action
        valid_actions = ["add", "remove", "swap"]
        if action not in valid_actions:
            return json.loads(json.dumps({
                "error": f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
            }))

        # Get build table
        build_table = data.get("build")
        if not build_table or not isinstance(build_table, dict):
            return json.loads(json.dumps({
                "error": "Build data not found in system"
            }))

        # Validate build exists
        if build_id not in build_table:
            return json.loads(json.dumps({
                "error": f"Build '{build_id}' not found"
            }))

        build = build_table[build_id]

        # Get product table
        product_table = data.get("product")
        if not product_table or not isinstance(product_table, dict):
            return json.loads(json.dumps({
                "error": "Product data not found in system"
            }))

        # Validate product exists
        if product_id not in product_table:
            return json.loads(json.dumps({
                "error": f"Product '{product_id}' not found"
            }))

        product = product_table[product_id]
        product_category = product.get("category")

        if not product_category:
            return json.loads(json.dumps({
                "error": f"Product '{product_id}' has no category"
            }))

        # Get current component IDs
        component_ids = build.get("componentIds", [])
        if not isinstance(component_ids, list):
            component_ids = []

        # Build a category map of current components
        category_map: Dict[str, List[str]] = {}
        for comp_id in component_ids:
            comp = product_table.get(comp_id)
            if comp:
                cat = comp.get("category")
                if cat:
                    if cat not in category_map:
                        category_map[cat] = []
                    category_map[cat].append(comp_id)

        # Get current timestamp
        now = get_now_iso_from_data(data)

        # Perform the action
        if action == "add":
            # Check if product already exists in build
            if product_id in component_ids:
                return json.loads(json.dumps({
                    "error": f"Product '{product_id}' already exists in build"
                }))

            # Check if category allows multiple instances
            if product_category not in MULTI_INSTANCE_CATEGORIES:
                # Check if this category already exists
                if product_category in category_map and len(category_map[product_category]) > 0:
                    return json.loads(json.dumps({
                        "error": f"Build already contains a '{product_category}' component. Category '{product_category}' does not allow multiple instances. Use 'swap' action to replace it.",
                        "existing_components": category_map[product_category]
                    }))

            # Add the product
            component_ids.append(product_id)
            build["componentIds"] = component_ids
            build["updatedAt"] = now

            return json.loads(json.dumps({
                "success": True,
                "action": "add",
                "build_id": build_id,
                "product_id": product_id,
                "build": build,
            }))

        elif action == "remove":
            # Check if product exists in build
            if product_id not in component_ids:
                return json.loads(json.dumps({
                    "error": f"Product '{product_id}' not found in build"
                }))

            # Remove the product (only first occurrence)
            component_ids.remove(product_id)
            build["componentIds"] = component_ids
            build["updatedAt"] = now

            return json.loads(json.dumps({
                "success": True,
                "action": "remove",
                "build_id": build_id,
                "product_id": product_id,
                "build": build,
            }))

        elif action == "swap":
            # Check if the category exists in the build
            if product_category not in category_map:
                return json.loads(json.dumps({
                    "error": f"No '{product_category}' component found in build to swap with"
                }))

            existing_components = category_map[product_category]

            # Check if all existing components are identical
            unique_existing = list(set(existing_components))

            if len(unique_existing) > 1:
                return json.loads(json.dumps({
                    "error": f"Multiple different '{product_category}' components found in build. Cannot determine which to swap.",
                    "existing_components": unique_existing
                }))

            # Get the component to swap out
            swap_out_id = unique_existing[0]

            # If swapping with itself, no change needed
            if swap_out_id == product_id:
                return json.loads(json.dumps({
                    "error": f"Product '{product_id}' is already in the build. No swap needed."
                }))

            # Replace all occurrences of the old component with the new one
            new_component_ids = []
            replacements_made = 0
            for comp_id in component_ids:
                if comp_id == swap_out_id:
                    new_component_ids.append(product_id)
                    replacements_made += 1
                else:
                    new_component_ids.append(comp_id)

            build["componentIds"] = new_component_ids
            build["updatedAt"] = now

            return json.loads(json.dumps({
                "success": True,
                "action": "swap",
                "build_id": build_id,
                "product_id": product_id,
                "swapped_out": swap_out_id,
                "replacements_made": replacements_made,
                "build": build,
            }))

        return json.loads(json.dumps({
            "error": "Unknown error occurred"
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_build",
                "description": f"Modify a build by adding, removing, or swapping a component. For non-memory/storage categories, only one component per category is allowed (use 'swap' to replace). Memory and storage can have multiple instances. When swapping, if multiple identical components exist in the same category, all will be replaced.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "build_id": {
                            "type": "string",
                            "description": "ID of the build to modify.",
                        },
                        "product_id": {
                            "type": "string",
                            "description": "Product ID to add, remove, or swap.",
                        },
                        "action": {
                            "type": "string",
                            "description": "Action to perform: 'add' (add new component), 'remove' (remove component), 'swap' (replace existing component in same category).",
                            "enum": ["add", "remove", "swap"],
                        },
                    },
                    "required": ["build_id", "product_id", "action"],
                },
            },
        }
