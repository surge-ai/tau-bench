import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_create_and_order_build import CreateAndOrderBuild


class TestCreateAndOrderBuild(unittest.TestCase):
    def setUp(self):
        """Set up test data with products, builds, and orders."""
        self.data: Dict[str, Any] = {
            "__now": "2025-01-15T12:00:00Z",
            "product": {
                "cryonix-z790-apex": {
                    "id": "cryonix-z790-apex",
                    "name": "Cryonix Z790 Apex",
                    "category": "motherboard",
                    "price": 299.99,
                },
                "novachip-pulse-10600k": {
                    "id": "novachip-pulse-10600k",
                    "name": "NovaChip Pulse 10600K",
                    "category": "cpu",
                    "price": 399.99,
                },
                "pyratech-graphforce-4070-16gb": {
                    "id": "pyratech-graphforce-4070-16gb",
                    "name": "PyraTech GraphForce 4070 16GB",
                    "category": "gpu",
                    "price": 599.99,
                },
                "hypervolt-ddr5-32gb-5600": {
                    "id": "hypervolt-ddr5-32gb-5600",
                    "name": "HyperVolt DDR5 32GB 5600",
                    "category": "memory",
                    "price": 149.99,
                },
                "dataforge-nvme-1tb-gen4": {
                    "id": "dataforge-nvme-1tb-gen4",
                    "name": "DataForge NVMe 1TB Gen4",
                    "category": "storage",
                    "price": 129.99,
                },
                "coreflow-750w-gold-modular": {
                    "id": "coreflow-750w-gold-modular",
                    "name": "CoreFlow 750W Gold Modular",
                    "category": "psu",
                    "price": 119.99,
                },
                "aeroshell-mid-tower-rgb": {
                    "id": "aeroshell-mid-tower-rgb",
                    "name": "AeroShell Mid Tower RGB",
                    "category": "case",
                    "price": 89.99,
                },
                "cryowave-aio-240mm": {
                    "id": "cryowave-aio-240mm",
                    "name": "CryoWave AIO 240mm",
                    "category": "cooling",
                    "price": 99.99,
                },
            },
            "build": {
                "configurator-monica-0": {
                    "ownerType": "customer",
                    "customerId": "monica-reynolds-71928",
                    "name": "Monica's Gaming Rig",
                    "componentIds": ["cryonix-z790-apex"],
                    "createdAt": "2021-08-15T14:22:00Z",
                    "updatedAt": "2021-08-15T14:22:00Z",
                },
            },
            "order": {},
        }

    def test_create_complete_build_and_order_success(self):
        """Test creating a complete build with all required categories and an order."""
        components = {
            "cpu": {"product_id": "novachip-pulse-10600k", "qty": 1},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "gpu": {"product_id": "pyratech-graphforce-4070-16gb", "qty": 1},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600", "qty": 2},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="John's Gaming Build",
            components=components,
        )

        self.assertTrue(result["success"])
        self.assertIn("build_id", result)
        self.assertIn("build", result)
        self.assertIn("order_id", result)
        self.assertIn("order", result)

        # Check build
        build = result["build"]
        self.assertEqual(build["ownerType"], "customer")
        self.assertEqual(build["customerId"], "john-doe-12345")
        self.assertEqual(build["name"], "John's Gaming Build")
        self.assertEqual(len(build["componentIds"]), 7)

        # Check order
        order = result["order"]
        self.assertEqual(order["customerId"], "john-doe-12345")
        self.assertEqual(order["buildId"], result["build_id"])
        self.assertEqual(order["status"], "pending")
        self.assertEqual(len(order["lineItems"]), 7)

        # Check line items structure
        memory_item = [item for item in order["lineItems"] if item["productId"] == "hypervolt-ddr5-32gb-5600"][0]
        self.assertEqual(memory_item["qty"], 2)

    def test_create_with_optional_cooling(self):
        """Test creating a build with optional cooling component."""
        components = {
            "cpu": {"product_id": "novachip-pulse-10600k"},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
            "cooling": {"product_id": "cryowave-aio-240mm"},  # Optional
        }

        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="John's Build with Cooling",
            components=components,
        )

        self.assertTrue(result["success"])
        self.assertEqual(len(result["build"]["componentIds"]), 7)

    def test_create_missing_required_category(self):
        """Test creating a build missing a required category."""
        components = {
            "cpu": {"product_id": "novachip-pulse-10600k"},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            # Missing: storage, psu, case
        }

        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="Incomplete Build",
            components=components,
        )

        self.assertIn("error", result)
        self.assertIn("missing required component categories", result["error"])
        self.assertIn("missing_categories", result)
        self.assertIn("storage", result["missing_categories"])
        self.assertIn("psu", result["missing_categories"])
        self.assertIn("case", result["missing_categories"])

    def test_create_invalid_owner_type(self):
        """Test creating a build with invalid ownerType."""
        components = {
            "cpu": {"product_id": "novachip-pulse-10600k"},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="invalid",
            name="Test Build",
            components=components,
        )

        self.assertIn("error", result)
        self.assertIn("Invalid ownerType", result["error"])

    def test_create_invalid_product_id(self):
        """Test creating a build with non-existent product ID."""
        components = {
            "cpu": {"product_id": "invalid-cpu-id"},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="Test Build",
            components=components,
        )

        self.assertIn("error", result)
        self.assertIn("Invalid product IDs", result["error"])
        self.assertIn("cpu: invalid-cpu-id", result["error"])

    def test_create_components_not_dict(self):
        """Test creating a build with components as non-dict."""
        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="Test Build",
            components="not a dict",
        )

        self.assertIn("error", result)
        self.assertIn("components must be a dictionary", result["error"])

    def test_create_component_missing_product_id(self):
        """Test creating a build with component missing product_id."""
        components = {
            "cpu": {"qty": 1},  # Missing product_id
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="Test Build",
            components=components,
        )

        self.assertIn("error", result)
        self.assertIn("missing required 'product_id' field", result["error"])

    def test_create_invalid_quantity(self):
        """Test creating a build with invalid quantity."""
        components = {
            "cpu": {"product_id": "novachip-pulse-10600k", "qty": -1},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="Test Build",
            components=components,
        )

        self.assertIn("error", result)
        self.assertIn("invalid quantity", result["error"])

    def test_create_increments_build_id(self):
        """Test that build IDs increment correctly for the same customer."""
        components = {
            "cpu": {"product_id": "novachip-pulse-10600k"},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        # Create first build for monica
        result1 = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="monica-reynolds-71928",
            ownerType="customer",
            name="Monica's Build 1",
            components=components,
        )

        self.assertTrue(result1["success"])
        self.assertEqual(result1["build_id"], "configurator-monica-1")

        # Create second build for monica
        result2 = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="monica-reynolds-71928",
            ownerType="customer",
            name="Monica's Build 2",
            components=components,
        )

        self.assertTrue(result2["success"])
        self.assertEqual(result2["build_id"], "configurator-monica-2")

    def test_create_increments_order_id(self):
        """Test that order IDs are generated correctly."""
        components = {
            "cpu": {"product_id": "novachip-pulse-10600k"},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        result1 = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="Build 1",
            components=components,
        )

        self.assertTrue(result1["success"])
        self.assertTrue(result1["order_id"].startswith("ord-250115-"))

        result2 = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="jane-doe-67890",
            ownerType="customer",
            name="Build 2",
            components=components,
        )

        self.assertTrue(result2["success"])
        self.assertNotEqual(result1["order_id"], result2["order_id"])

    def test_create_internal_build(self):
        """Test creating an internal build."""
        components = {
            "cpu": {"product_id": "novachip-pulse-10600k"},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="internal-template",
            ownerType="internal",
            name="Base Gaming Template",
            components=components,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["build"]["ownerType"], "internal")

    def test_create_no_product_table(self):
        """Test creating a build when product table doesn't exist."""
        data_no_products = {
            "__now": "2025-01-15T12:00:00Z",
            "build": {},
            "order": {},
        }

        components = {
            "cpu": {"product_id": "some-product"},
        }

        result = CreateAndOrderBuild.invoke(
            data_no_products,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="Test Build",
            components=components,
        )

        self.assertIn("error", result)
        self.assertIn("Product data not found", result["error"])

    def test_create_tables_created_if_missing(self):
        """Test that build and order tables are created if they don't exist."""
        data_no_tables = {
            "__now": "2025-01-15T12:00:00Z",
            "product": self.data["product"],
        }

        components = {
            "cpu": {"product_id": "novachip-pulse-10600k"},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        result = CreateAndOrderBuild.invoke(
            data_no_tables,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="First Build",
            components=components,
        )

        self.assertTrue(result["success"])
        self.assertIn("build", data_no_tables)
        self.assertIn("order", data_no_tables)
        self.assertIn(result["build_id"], data_no_tables["build"])
        self.assertIn(result["order_id"], data_no_tables["order"])

    def test_order_has_build_id_reference(self):
        """Test that the created order references the build."""
        components = {
            "cpu": {"product_id": "novachip-pulse-10600k"},
            "motherboard": {"product_id": "cryonix-z790-apex"},
            "memory": {"product_id": "hypervolt-ddr5-32gb-5600"},
            "storage": {"product_id": "dataforge-nvme-1tb-gen4"},
            "psu": {"product_id": "coreflow-750w-gold-modular"},
            "case": {"product_id": "aeroshell-mid-tower-rgb"},
        }

        result = CreateAndOrderBuild.invoke(
            self.data,
            customer_id="john-doe-12345",
            ownerType="customer",
            name="Test Build",
            components=components,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["order"]["buildId"], result["build_id"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CreateAndOrderBuild.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "create_and_order_build")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])

        params = info["function"]["parameters"]
        self.assertIn("customer_id", params["properties"])
        self.assertIn("ownerType", params["properties"])
        self.assertIn("name", params["properties"])
        self.assertIn("components", params["properties"])

        # Check required fields
        required = params["required"]
        self.assertIn("customer_id", required)
        self.assertIn("ownerType", required)
        self.assertIn("name", required)
        self.assertIn("components", required)


if __name__ == "__main__":
    unittest.main()
