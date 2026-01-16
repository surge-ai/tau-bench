import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_create_order import (
    CreateOrder,
    VALID_STATUSES,
    VALID_CARRIERS,
    VALID_SERVICES,
)


class TestCreateOrder(unittest.TestCase):
    def setUp(self):
        """Set up test data with customers, products, and builds."""
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
                "ram1": {
                    "id": "ram1",
                    "name": "Corsair Vengeance 32GB",
                    "category": "memory",
                    "price": 129.99,
                },
            },
            "build": {
                "build1": {
                    "id": "build1",
                    "name": "Gaming PC",
                    "customerId": "cust1",
                    "productIds": ["cpu1", "gpu1"],
                },
            },
        }

    def test_create_order_basic(self):
        """Test creating a basic order."""
        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
        )

        # Check that order was created with correct fields
        self.assertIn("id", result_dict)
        self.assertTrue(result_dict["id"].startswith("ord_"))
        self.assertEqual(result_dict["customerId"], "cust1")
        self.assertEqual(result_dict["lineItems"], [{"productId": "cpu1", "qty": 1}])
        self.assertEqual(result_dict["status"], "pending")
        self.assertIn("createdAt", result_dict)
        self.assertIn("updatedAt", result_dict)

    def test_create_order_multiple_items(self):
        """Test creating order with multiple line items."""
        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[
                {"productId": "cpu1", "qty": 1},
                {"productId": "gpu1", "qty": 1},
                {"productId": "ram1", "qty": 2},
            ],
        )

        self.assertEqual(len(result_dict["lineItems"]), 3)
        # Check quantities
        items_by_product = {item["productId"]: item["qty"] for item in result_dict["lineItems"]}
        self.assertEqual(items_by_product["cpu1"], 1)
        self.assertEqual(items_by_product["gpu1"], 1)
        self.assertEqual(items_by_product["ram1"], 2)

    def test_create_order_with_status(self):
        """Test creating order with specific status."""
        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
            status="paid",
        )

        self.assertEqual(result_dict["status"], "paid")

    def test_create_order_all_statuses(self):
        """Test all valid status values."""
        for status in VALID_STATUSES:
            # Reset order table
            self.data["order"] = {}

            result_dict = CreateOrder.invoke(
                self.data,
                customer_id="cust1",
                line_items=[{"productId": "cpu1", "qty": 1}],
                status=status,
            )

            self.assertEqual(result_dict["status"], status)

    def test_create_order_with_shipping(self):
        """Test creating order with shipping information."""
        shipping_address = {
            "line1": "123 Main St",
            "line2": "Apt 4",
            "city": "Austin",
            "region": "TX",
            "postalCode": "78701",
            "country": "US",
        }

        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
            shipping_address=shipping_address,
            shipping_carrier="FedEx Express",
            shipping_service="express",
        )

        self.assertIn("shipping", result_dict)
        self.assertEqual(result_dict["shipping"]["address"], shipping_address)
        self.assertEqual(result_dict["shipping"]["carrier"], "FedEx Express")
        self.assertEqual(result_dict["shipping"]["service"], "express")

    def test_create_order_with_build_id(self):
        """Test creating order with build reference."""
        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
            build_id="build1",
        )

        self.assertEqual(result_dict["buildId"], "build1")

    def test_create_order_invalid_customer(self):
        """Test creating order for non-existent customer."""
        result = CreateOrder.invoke(
            self.data,
            customer_id="nonexistent",
            line_items=[{"productId": "cpu1", "qty": 1}],
        )
        self.assertIn("error", result)
        self.assertIn("nonexistent", result["error"])

    def test_create_order_invalid_product(self):
        """Test creating order with non-existent product."""
        result = CreateOrder.invoke(
            self.data,
                customer_id="cust1",
                line_items=[{"productId": "nonexistent", "qty": 1}],
            )
        self.assertIn("error", result)
        self.assertIn("nonexistent", result["error"])

    def test_create_order_multiple_invalid_products(self):
        """Test that all non-existent products are listed in error."""
        result = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[
                {"productId": "cpu1", "qty": 1},
                {"productId": "bad1", "qty": 1},
                {"productId": "bad2", "qty": 1},
                ],
            )

        self.assertIn("bad1", result["error"])
        self.assertIn("bad2", result["error"])
        self.assertIn("Products not found", result["error"])

    def test_create_order_invalid_build(self):
        """Test creating order with non-existent build."""
        
        result = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
            build_id="nonexistent",
        )
        self.assertIn("error", result)
        self.assertIn("nonexistent", result["error"])

    def test_create_order_empty_line_items(self):
        """Test creating order with empty line items."""
        result = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[],
        )
        self.assertIn("error", result)
        self.assertIn("at least one line item", result["error"])

    def test_create_order_invalid_status(self):
        """Test creating order with invalid status."""
        result = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
            status="invalid_status",
        )
        self.assertIn("error", result)
        self.assertIn("Invalid status", result["error"])

    def test_create_order_invalid_carrier(self):
        """Test creating order with invalid carrier."""
        result = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
            shipping_carrier="invalid_carrier",
        )
        self.assertIn("error", result)
        self.assertIn("Invalid shipping_carrier", result["error"])

    def test_create_order_invalid_service(self):
        """Test creating order with invalid service."""
        result = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
            shipping_service="invalid_service",
        )
        self.assertIn("error", result)
        self.assertIn("Invalid shipping_service", result["error"])

    def test_create_order_mutates_data_in_place(self):
        """Test that the tool adds order to data dict."""
        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
        )

        # Check that order was added to data
        self.assertIn("order", self.data)
        self.assertIn(result_dict["id"], self.data["order"])

    def test_create_order_deterministic_id(self):
        """Test that the same inputs produce the same ID."""
        result1 = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
        )

        # Reset order table
        self.data["order"] = {}

        result2 = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
        )

        # Same inputs should produce same ID
        self.assertEqual(result1["id"], result2["id"])

    def test_create_order_different_inputs_different_id(self):
        """Test that different inputs produce different IDs."""
        result1 = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
        )

        result2 = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 2}],  # Different qty
        )

        # Different inputs should produce different ID
        self.assertNotEqual(result1["id"], result2["id"])

    def test_create_order_uses_custom_timestamp(self):
        """Test that order uses custom timestamp from data if provided."""
        self.data["__now"] = "2025-06-15T12:00:00Z"

        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
        )

        self.assertEqual(result_dict["createdAt"], "2025-06-15T12:00:00Z")
        self.assertEqual(result_dict["updatedAt"], "2025-06-15T12:00:00Z")

    def test_create_order_defaults_to_constant_timestamp(self):
        """Test that order uses constant timestamp when not provided."""
        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
        )

        self.assertEqual(result_dict["createdAt"], "1970-01-01T00:00:00Z")
        self.assertEqual(result_dict["updatedAt"], "1970-01-01T00:00:00Z")

    def test_create_order_creates_table_if_missing(self):
        """Test that order table is created if not present."""
        # Remove order table if exists
        self.data.pop("order", None)

        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[{"productId": "cpu1", "qty": 1}],
        )

        self.assertIn("order", self.data)
        self.assertIn(result_dict["id"], self.data["order"])

    def test_create_order_normalizes_line_items(self):
        """Test that line items are normalized to consistent format."""
        # Use alternative field names
        result_dict = CreateOrder.invoke(
            self.data,
            customer_id="cust1",
            line_items=[
                {"product_id": "cpu1", "quantity": 2},  # snake_case and 'quantity'
            ],
        )

        # Should be normalized to camelCase
        self.assertEqual(result_dict["lineItems"][0]["productId"], "cpu1")
        self.assertEqual(result_dict["lineItems"][0]["qty"], 2)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CreateOrder.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "createOrder")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])

        properties = info["function"]["parameters"]["properties"]
        self.assertIn("customer_id", properties)
        self.assertIn("line_items", properties)
        self.assertIn("status", properties)
        self.assertIn("shipping_address", properties)
        self.assertIn("shipping_carrier", properties)
        self.assertIn("shipping_service", properties)
        self.assertIn("build_id", properties)

        # Check enums are set correctly
        self.assertEqual(properties["status"]["enum"], VALID_STATUSES)
        self.assertEqual(properties["shipping_carrier"]["enum"], VALID_CARRIERS)
        self.assertEqual(properties["shipping_service"]["enum"], VALID_SERVICES)

        required = info["function"]["parameters"]["required"]
        self.assertIn("customer_id", required)
        self.assertIn("line_items", required)
        self.assertNotIn("status", required)
        self.assertNotIn("shipping_address", required)
        self.assertNotIn("build_id", required)


if __name__ == "__main__":
    unittest.main()
