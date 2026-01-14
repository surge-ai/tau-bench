import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_create_build import CreateBuild


class TestCreateBuild(unittest.TestCase):
    def setUp(self):
        """Set up test data with customers and products."""
        self.data: Dict[str, Any] = {
            "customer": {
                "cust1": {
                    "id": "cust1",
                    "name": "John Doe",
                    "email": "john@example.com",
                },
                "cust2": {
                    "id": "cust2",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                },
            },
            "product": {
                "cpu1": {
                    "id": "cpu1",
                    "name": "Intel Core i9",
                    "category": "cpu",
                    "price": 499.99,
                },
                "gpu1": {
                    "id": "gpu1",
                    "name": "NVIDIA RTX 4090",
                    "category": "gpu",
                    "price": 1599.99,
                },
                "mobo1": {
                    "id": "mobo1",
                    "name": "ASUS ROG Maximus",
                    "category": "motherboard",
                    "price": 599.99,
                },
                "ram1": {
                    "id": "ram1",
                    "name": "Corsair Vengeance 32GB",
                    "category": "memory",
                    "price": 129.99,
                },
            },
        }

    def test_create_build_basic(self):
        """Test creating a basic build."""
        result_dict = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        # Check that build was created with correct fields
        self.assertIn("id", result_dict)
        self.assertTrue(result_dict["id"].startswith("build_"))
        self.assertEqual(result_dict["name"], "Gaming PC")
        self.assertEqual(result_dict["customerId"], "cust1")
        self.assertEqual(result_dict["productIds"], ["cpu1", "gpu1"])
        self.assertIn("createdAt", result_dict)
        self.assertIn("updatedAt", result_dict)

    def test_create_build_sorts_product_ids(self):
        """Test that product IDs are sorted."""
        result_dict = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["ram1", "cpu1", "gpu1", "mobo1"],
        )

        # Product IDs should be sorted
        self.assertEqual(result_dict["productIds"], ["cpu1", "gpu1", "mobo1", "ram1"])

    def test_create_build_deterministic_id(self):
        """Test that the same inputs produce the same ID."""
        result1 = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        # Reset build table
        self.data["build"] = {}

        result2 = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        # Same inputs should produce same ID
        self.assertEqual(result1["id"], result2["id"])

    def test_create_build_different_order_same_id(self):
        """Test that product order doesn't affect ID."""
        result1 = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        # Reset build table
        self.data["build"] = {}

        result2 = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["gpu1", "cpu1"],  # Different order
        )

        # Same products in different order should produce same ID
        self.assertEqual(result1["id"], result2["id"])

    def test_create_build_different_inputs_different_id(self):
        """Test that different inputs produce different IDs."""
        result1 = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        result2 = CreateBuild.invoke(
            self.data,
            name="Workstation",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        # Different name should produce different ID
        self.assertNotEqual(result1["id"], result2["id"])

    def test_create_build_invalid_customer(self):
        """Test creating build for non-existent customer."""
        with self.assertRaises(ValueError) as context:
            CreateBuild.invoke(
                self.data,
                name="Gaming PC",
                customer_id="nonexistent",
                product_ids=["cpu1", "gpu1"],
            )

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("not found", str(context.exception))

    def test_create_build_invalid_product(self):
        """Test creating build with non-existent product."""
        with self.assertRaises(ValueError) as context:
            CreateBuild.invoke(
                self.data,
                name="Gaming PC",
                customer_id="cust1",
                product_ids=["cpu1", "nonexistent"],
            )

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("not found", str(context.exception))

    def test_create_build_multiple_invalid_products(self):
        """Test that all non-existent products are listed in error."""
        with self.assertRaises(ValueError) as context:
            CreateBuild.invoke(
                self.data,
                name="Gaming PC",
                customer_id="cust1",
                product_ids=["cpu1", "bad1", "gpu1", "bad2"],
            )

        error_msg = str(context.exception)
        self.assertIn("bad1", error_msg)
        self.assertIn("bad2", error_msg)
        self.assertIn("Products not found", error_msg)

    def test_create_build_mutates_data_in_place(self):
        """Test that the tool adds build to data dict."""
        result_dict = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        # Check that build was added to data
        self.assertIn("build", self.data)
        self.assertIn(result_dict["id"], self.data["build"])

    def test_create_build_uses_custom_timestamp(self):
        """Test that build uses custom timestamp from data if provided."""
        self.data["__now"] = "2025-06-15T12:00:00Z"

        result_dict = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        self.assertEqual(result_dict["createdAt"], "2025-06-15T12:00:00Z")
        self.assertEqual(result_dict["updatedAt"], "2025-06-15T12:00:00Z")

    def test_create_build_defaults_to_constant_timestamp(self):
        """Test that build uses constant timestamp when not provided."""
        result_dict = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        self.assertEqual(result_dict["createdAt"], "1970-01-01T00:00:00Z")
        self.assertEqual(result_dict["updatedAt"], "1970-01-01T00:00:00Z")

    def test_create_build_empty_product_list(self):
        """Test creating build with empty product list."""
        result_dict = CreateBuild.invoke(
            self.data,
            name="Empty Build",
            customer_id="cust1",
            product_ids=[],
        )

        self.assertEqual(result_dict["productIds"], [])

    def test_create_build_creates_build_table_if_missing(self):
        """Test that build table is created if not present."""
        # Remove build table if exists
        self.data.pop("build", None)

        result_dict = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        self.assertIn("build", self.data)
        self.assertIn(result_dict["id"], self.data["build"])

    def test_create_build_multiple_builds(self):
        """Test creating multiple builds."""
        result1 = CreateBuild.invoke(
            self.data,
            name="Gaming PC",
            customer_id="cust1",
            product_ids=["cpu1", "gpu1"],
        )

        result2 = CreateBuild.invoke(
            self.data,
            name="Workstation",
            customer_id="cust2",
            product_ids=["cpu1", "mobo1", "ram1"],
        )

        # Both builds should exist
        self.assertEqual(len(self.data["build"]), 2)
        self.assertIn(result1["id"], self.data["build"])
        self.assertIn(result2["id"], self.data["build"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CreateBuild.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "createBuild")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("name", info["function"]["parameters"]["properties"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("product_ids", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("name", required)
        self.assertIn("customer_id", required)
        self.assertIn("product_ids", required)


if __name__ == "__main__":
    unittest.main()
