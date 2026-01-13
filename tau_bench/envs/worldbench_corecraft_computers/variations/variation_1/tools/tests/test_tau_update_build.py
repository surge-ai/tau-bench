import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_update_build import UpdateBuild


class TestUpdateBuild(unittest.TestCase):
    def setUp(self):
        """Set up test data with builds and products."""
        self.data: Dict[str, Any] = {
            "customer": {
                "cust1": {
                    "id": "cust1",
                    "name": "John Doe",
                    "email": "john@example.com",
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
                "psu1": {
                    "id": "psu1",
                    "name": "Corsair RM1000x",
                    "category": "psu",
                    "price": 189.99,
                },
            },
            "build": {
                "build1": {
                    "id": "build1",
                    "name": "Gaming PC",
                    "customerId": "cust1",
                    "productIds": ["cpu1", "gpu1"],
                    "createdAt": "2025-01-01T00:00:00Z",
                    "updatedAt": "2025-01-01T00:00:00Z",
                },
                "build2": {
                    "id": "build2",
                    "name": "Workstation",
                    "customerId": "cust1",
                    "productIds": ["cpu1", "mobo1", "ram1"],
                    "createdAt": "2025-01-02T00:00:00Z",
                    "updatedAt": "2025-01-02T00:00:00Z",
                },
            },
        }

    def test_update_build_name(self):
        """Test updating build name."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            name="Ultimate Gaming Rig",
        )

        self.assertEqual(result_dict["name"], "Ultimate Gaming Rig")
        self.assertEqual(self.data["build"]["build1"]["name"], "Ultimate Gaming Rig")

    def test_update_build_add_products(self):
        """Test adding products to build."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            add_product_ids=["mobo1", "ram1"],
        )

        # Products should be sorted
        self.assertEqual(result_dict["productIds"], ["cpu1", "gpu1", "mobo1", "ram1"])
        self.assertEqual(self.data["build"]["build1"]["productIds"], ["cpu1", "gpu1", "mobo1", "ram1"])

    def test_update_build_remove_products(self):
        """Test removing products from build."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            remove_product_ids=["gpu1"],
        )

        self.assertEqual(result_dict["productIds"], ["cpu1"])
        self.assertEqual(self.data["build"]["build1"]["productIds"], ["cpu1"])

    def test_update_build_add_and_remove_products(self):
        """Test adding and removing products in same call."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            add_product_ids=["mobo1", "ram1"],
            remove_product_ids=["gpu1"],
        )

        # Should have cpu1, mobo1, ram1 (gpu1 removed)
        self.assertEqual(result_dict["productIds"], ["cpu1", "mobo1", "ram1"])

    def test_update_build_remove_nonexistent_product(self):
        """Test removing product not in build (no error)."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            remove_product_ids=["nonexistent"],
        )

        # Should not change anything
        self.assertEqual(result_dict["productIds"], ["cpu1", "gpu1"])

    def test_update_build_add_duplicate_product(self):
        """Test adding product already in build (no duplicate)."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            add_product_ids=["cpu1"],  # Already in build
        )

        # Should not duplicate
        self.assertEqual(result_dict["productIds"], ["cpu1", "gpu1"])

    def test_update_build_invalid_build_id(self):
        """Test updating non-existent build."""
        with self.assertRaises(ValueError) as context:
            UpdateBuild.invoke(
                self.data,
                build_id="nonexistent",
                name="New Name",
            )

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("not found", str(context.exception))

    def test_update_build_invalid_product_to_add(self):
        """Test adding non-existent product."""
        with self.assertRaises(ValueError) as context:
            UpdateBuild.invoke(
                self.data,
                build_id="build1",
                add_product_ids=["nonexistent"],
            )

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("not found", str(context.exception))

    def test_update_build_missing_build_table(self):
        """Test updating when build table doesn't exist."""
        data_no_builds = {"customer": {}, "product": {}}

        with self.assertRaises(ValueError) as context:
            UpdateBuild.invoke(
                data_no_builds,
                build_id="build1",
                name="New Name",
            )

        self.assertIn("table not found", str(context.exception).lower())

    def test_update_build_updates_timestamp(self):
        """Test that updatedAt is updated."""
        self.data["__now"] = "2025-06-15T12:00:00Z"

        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            name="Updated Build",
        )

        self.assertEqual(result_dict["updatedAt"], "2025-06-15T12:00:00Z")
        # createdAt should not change
        self.assertEqual(result_dict["createdAt"], "2025-01-01T00:00:00Z")

    def test_update_build_default_timestamp(self):
        """Test that updatedAt defaults to constant."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            name="Updated Build",
        )

        self.assertEqual(result_dict["updatedAt"], "1970-01-01T00:00:00Z")

    def test_update_build_mutates_data_in_place(self):
        """Test that the tool mutates data in place."""
        initial_build = self.data["build"]["build1"]

        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            name="Updated Build",
        )

        # Should be same object
        self.assertIs(initial_build, self.data["build"]["build1"])
        self.assertEqual(initial_build["name"], "Updated Build")

    def test_update_build_other_builds_unchanged(self):
        """Test that other builds are not affected."""
        initial_build2_name = self.data["build"]["build2"]["name"]

        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            name="Updated Build",
        )

        # build2 should be unchanged
        self.assertEqual(self.data["build"]["build2"]["name"], initial_build2_name)

    def test_update_build_preserves_other_fields(self):
        """Test that other fields are preserved."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            name="Updated Build",
        )

        # Other fields should be preserved
        self.assertEqual(result_dict["id"], "build1")
        self.assertEqual(result_dict["customerId"], "cust1")
        self.assertEqual(result_dict["createdAt"], "2025-01-01T00:00:00Z")

    def test_update_build_no_changes(self):
        """Test updating with no changes."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
        )

        # Should return the build with only updatedAt changed
        self.assertEqual(result_dict["name"], "Gaming PC")
        self.assertEqual(result_dict["productIds"], ["cpu1", "gpu1"])

    def test_update_build_products_sorted(self):
        """Test that products remain sorted after update."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            add_product_ids=["psu1", "mobo1"],  # Add out of order
        )

        # Products should be sorted
        self.assertEqual(result_dict["productIds"], ["cpu1", "gpu1", "mobo1", "psu1"])

    def test_update_build_name_and_products(self):
        """Test updating name and products together."""
        result_dict = UpdateBuild.invoke(
            self.data,
            build_id="build1",
            name="Complete Build",
            add_product_ids=["mobo1"],
            remove_product_ids=["gpu1"],
        )

        self.assertEqual(result_dict["name"], "Complete Build")
        self.assertEqual(result_dict["productIds"], ["cpu1", "mobo1"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = UpdateBuild.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "updateBuild")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("build_id", info["function"]["parameters"]["properties"])
        self.assertIn("name", info["function"]["parameters"]["properties"])
        self.assertIn("add_product_ids", info["function"]["parameters"]["properties"])
        self.assertIn("remove_product_ids", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("build_id", required)
        self.assertNotIn("name", required)
        self.assertNotIn("add_product_ids", required)
        self.assertNotIn("remove_product_ids", required)


if __name__ == "__main__":
    unittest.main()
