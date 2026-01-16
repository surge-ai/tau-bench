import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_modify_build import ModifyBuild


class TestModifyBuild(unittest.TestCase):
    def setUp(self):
        """Set up test data with products and builds."""
        self.data: Dict[str, Any] = {
            "__now": "2025-01-15T12:00:00Z",
            "product": {
                "cpu-1": {"id": "cpu-1", "name": "CPU 1", "category": "cpu", "price": 399.99},
                "cpu-2": {"id": "cpu-2", "name": "CPU 2", "category": "cpu", "price": 499.99},
                "gpu-1": {"id": "gpu-1", "name": "GPU 1", "category": "gpu", "price": 599.99},
                "gpu-2": {"id": "gpu-2", "name": "GPU 2", "category": "gpu", "price": 799.99},
                "mobo-1": {"id": "mobo-1", "name": "Motherboard 1", "category": "motherboard", "price": 299.99},
                "mobo-2": {"id": "mobo-2", "name": "Motherboard 2", "category": "motherboard", "price": 399.99},
                "memory-1": {"id": "memory-1", "name": "Memory 1", "category": "memory", "price": 149.99},
                "memory-2": {"id": "memory-2", "name": "Memory 2", "category": "memory", "price": 199.99},
                "storage-1": {"id": "storage-1", "name": "Storage 1", "category": "storage", "price": 129.99},
                "storage-2": {"id": "storage-2", "name": "Storage 2", "category": "storage", "price": 179.99},
                "psu-1": {"id": "psu-1", "name": "PSU 1", "category": "psu", "price": 119.99},
                "cooling-1": {"id": "cooling-1", "name": "Cooling 1", "category": "cooling", "price": 99.99},
            },
            "build": {
                "build-1": {
                    "ownerType": "customer",
                    "customerId": "customer-1",
                    "name": "Test Build",
                    "componentIds": ["cpu-1", "gpu-1", "mobo-1", "memory-1", "storage-1"],
                    "createdAt": "2025-01-01T00:00:00Z",
                    "updatedAt": "2025-01-01T00:00:00Z",
                },
                "build-2": {
                    "ownerType": "customer",
                    "customerId": "customer-2",
                    "name": "Multi-Memory Build",
                    "componentIds": ["cpu-1", "mobo-1", "memory-1", "memory-1", "storage-1"],
                    "createdAt": "2025-01-01T00:00:00Z",
                    "updatedAt": "2025-01-01T00:00:00Z",
                },
            },
        }

    def test_add_component_success(self):
        """Test adding a new component to a build."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="psu-1",
            action="add",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "add")
        self.assertEqual(result["product_id"], "psu-1")
        self.assertIn("psu-1", result["build"]["componentIds"])
        self.assertEqual(result["build"]["updatedAt"], "2025-01-15T12:00:00Z")

    def test_add_memory_multiple_allowed(self):
        """Test adding multiple memory components (allowed)."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="memory-2",
            action="add",
        )

        self.assertTrue(result["success"])
        self.assertIn("memory-1", result["build"]["componentIds"])
        self.assertIn("memory-2", result["build"]["componentIds"])

    def test_add_storage_multiple_allowed(self):
        """Test adding multiple storage components (allowed)."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="storage-2",
            action="add",
        )

        self.assertTrue(result["success"])
        self.assertIn("storage-1", result["build"]["componentIds"])
        self.assertIn("storage-2", result["build"]["componentIds"])

    def test_add_duplicate_component_error(self):
        """Test adding a component that already exists in build."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="cpu-1",
            action="add",
        )

        self.assertIn("error", result)
        self.assertIn("already exists", result["error"])

    def test_add_second_cpu_not_allowed(self):
        """Test adding a second CPU (not allowed)."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="cpu-2",
            action="add",
        )

        self.assertIn("error", result)
        self.assertIn("already contains a 'cpu' component", result["error"])
        self.assertIn("existing_components", result)
        self.assertIn("cpu-1", result["existing_components"])

    def test_add_second_gpu_not_allowed(self):
        """Test adding a second GPU (not allowed)."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="gpu-2",
            action="add",
        )

        self.assertIn("error", result)
        self.assertIn("already contains a 'gpu' component", result["error"])

    def test_add_invalid_product(self):
        """Test adding a non-existent product."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="invalid-product",
            action="add",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_add_invalid_build(self):
        """Test adding to a non-existent build."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="invalid-build",
            product_id="psu-1",
            action="add",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_remove_component_success(self):
        """Test removing a component from a build."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="gpu-1",
            action="remove",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "remove")
        self.assertEqual(result["product_id"], "gpu-1")
        self.assertNotIn("gpu-1", result["build"]["componentIds"])
        self.assertEqual(result["build"]["updatedAt"], "2025-01-15T12:00:00Z")

    def test_remove_component_not_in_build(self):
        """Test removing a component that's not in the build."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="psu-1",
            action="remove",
        )

        self.assertIn("error", result)
        self.assertIn("not found in build", result["error"])

    def test_swap_component_success(self):
        """Test swapping a component."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="cpu-2",
            action="swap",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "swap")
        self.assertEqual(result["product_id"], "cpu-2")
        self.assertEqual(result["swapped_out"], "cpu-1")
        self.assertNotIn("cpu-1", result["build"]["componentIds"])
        self.assertIn("cpu-2", result["build"]["componentIds"])
        self.assertEqual(result["replacements_made"], 1)

    def test_swap_gpu_success(self):
        """Test swapping a GPU."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="gpu-2",
            action="swap",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["swapped_out"], "gpu-1")
        self.assertNotIn("gpu-1", result["build"]["componentIds"])
        self.assertIn("gpu-2", result["build"]["componentIds"])

    def test_swap_no_existing_component(self):
        """Test swapping when no component of that category exists."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="psu-1",
            action="swap",
        )

        self.assertIn("error", result)
        self.assertIn("No 'psu' component found", result["error"])

    def test_swap_with_same_component(self):
        """Test swapping a component with itself."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="cpu-1",
            action="swap",
        )

        self.assertIn("error", result)
        self.assertIn("already in the build", result["error"])

    def test_swap_multiple_identical_components(self):
        """Test swapping when multiple identical components exist."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-2",
            product_id="memory-2",
            action="swap",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["swapped_out"], "memory-1")
        self.assertEqual(result["replacements_made"], 2)
        # Check that all memory-1 instances were replaced
        self.assertNotIn("memory-1", result["build"]["componentIds"])
        # Count memory-2 instances
        memory_2_count = result["build"]["componentIds"].count("memory-2")
        self.assertEqual(memory_2_count, 2)

    def test_swap_multiple_different_components_error(self):
        """Test swapping when multiple different components of same category exist."""
        # Add a different memory to build-2
        self.data["build"]["build-2"]["componentIds"].append("memory-2")

        result = ModifyBuild.invoke(
            self.data,
            build_id="build-2",
            product_id="memory-1",
            action="swap",
        )

        self.assertIn("error", result)
        self.assertIn("Multiple different", result["error"])
        self.assertIn("existing_components", result)

    def test_invalid_action(self):
        """Test with invalid action."""
        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="cpu-1",
            action="invalid",
        )

        self.assertIn("error", result)
        self.assertIn("Invalid action", result["error"])

    def test_no_build_table(self):
        """Test when build table doesn't exist."""
        data_no_builds = {
            "__now": "2025-01-15T12:00:00Z",
            "product": self.data["product"],
        }

        result = ModifyBuild.invoke(
            data_no_builds,
            build_id="build-1",
            product_id="cpu-1",
            action="add",
        )

        self.assertIn("error", result)
        self.assertIn("Build data not found", result["error"])

    def test_no_product_table(self):
        """Test when product table doesn't exist."""
        data_no_products = {
            "__now": "2025-01-15T12:00:00Z",
            "build": self.data["build"],
        }

        result = ModifyBuild.invoke(
            data_no_products,
            build_id="build-1",
            product_id="cpu-1",
            action="add",
        )

        self.assertIn("error", result)
        self.assertIn("Product data not found", result["error"])

    def test_add_updates_timestamp(self):
        """Test that add action updates timestamp."""
        old_timestamp = self.data["build"]["build-1"]["updatedAt"]

        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="psu-1",
            action="add",
        )

        self.assertTrue(result["success"])
        self.assertNotEqual(result["build"]["updatedAt"], old_timestamp)
        self.assertEqual(result["build"]["updatedAt"], "2025-01-15T12:00:00Z")

    def test_remove_updates_timestamp(self):
        """Test that remove action updates timestamp."""
        old_timestamp = self.data["build"]["build-1"]["updatedAt"]

        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="gpu-1",
            action="remove",
        )

        self.assertTrue(result["success"])
        self.assertNotEqual(result["build"]["updatedAt"], old_timestamp)

    def test_swap_updates_timestamp(self):
        """Test that swap action updates timestamp."""
        old_timestamp = self.data["build"]["build-1"]["updatedAt"]

        result = ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="cpu-2",
            action="swap",
        )

        self.assertTrue(result["success"])
        self.assertNotEqual(result["build"]["updatedAt"], old_timestamp)

    def test_build_persists_changes(self):
        """Test that changes persist in the data structure."""
        ModifyBuild.invoke(
            self.data,
            build_id="build-1",
            product_id="psu-1",
            action="add",
        )

        # Verify directly in data
        self.assertIn("psu-1", self.data["build"]["build-1"]["componentIds"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = ModifyBuild.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "modify_build")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])

        params = info["function"]["parameters"]
        self.assertIn("build_id", params["properties"])
        self.assertIn("product_id", params["properties"])
        self.assertIn("action", params["properties"])

        # Check required fields
        required = params["required"]
        self.assertIn("build_id", required)
        self.assertIn("product_id", required)
        self.assertIn("action", required)

        # Check enum for action
        self.assertEqual(params["properties"]["action"]["enum"], ["add", "remove", "swap"])


if __name__ == "__main__":
    unittest.main()
