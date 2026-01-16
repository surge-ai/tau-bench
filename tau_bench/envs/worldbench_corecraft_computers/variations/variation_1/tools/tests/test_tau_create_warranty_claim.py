import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_create_warranty_claim import (
    CreateWarrantyClaim,
    VALID_STATUSES,
    VALID_REASONS,
    VALID_DENIAL_REASONS,
    BUILD_PRODUCT_CATEGORIES,
)


class TestCreateWarrantyClaim(unittest.TestCase):
    def setUp(self):
        """Set up test data with customers, products, and orders."""
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
                "prod1": {
                    "id": "prod1",
                    "name": "Intel Core i9",
                    "category": "cpu",
                    "price": 499.99,
                    "warrantyMonths": 36,
                },
                "prod2": {
                    "id": "prod2",
                    "name": "NVIDIA RTX 4090",
                    "category": "gpu",
                    "price": 1599.99,
                    "warrantyMonths": 24,
                },
                "prebuilt1": {
                    "id": "prebuilt1",
                    "name": "CoreCraft Gaming Pro",
                    "category": "prebuilt",
                    "price": 2499.99,
                    "warrantyMonths": 24,
                },
                "workstation1": {
                    "id": "workstation1",
                    "name": "CoreCraft Workstation X",
                    "category": "workstation",
                    "price": 4999.99,
                    "warrantyMonths": 36,
                },
            },
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "cust1",
                    "status": "fulfilled",
                    "lineItems": [
                        {"productId": "prod1", "qty": 1, "price": 499.99},
                    ],
                },
                "order2": {
                    "id": "order2",
                    "customerId": "cust2",
                    "status": "fulfilled",
                    "lineItems": [
                        {"productId": "prod2", "qty": 1, "price": 1599.99},
                    ],
                },
            },
        }

    def test_create_warranty_claim_basic(self):
        """Test creating a basic warranty claim."""
        result_dict = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        # Check that claim was created with correct fields
        self.assertIn("id", result_dict)
        self.assertTrue(result_dict["id"].startswith("warranty_claim_"))
        self.assertEqual(result_dict["productId"], "prod1")
        self.assertEqual(result_dict["orderId"], "order1")
        self.assertEqual(result_dict["customerId"], "cust1")
        self.assertEqual(result_dict["reason"], "defect")
        self.assertEqual(result_dict["status"], "pending_review")
        self.assertIsNone(result_dict["denialReason"])
        self.assertIsNone(result_dict["notes"])
        self.assertIn("createdAt", result_dict)
        self.assertIn("updatedAt", result_dict)

    def test_create_warranty_claim_with_status(self):
        """Test creating claim with specific status."""
        result_dict = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="malfunction",
            status="accepted",
        )

        self.assertEqual(result_dict["status"], "accepted")

    def test_create_warranty_claim_denied_with_reason(self):
        """Test creating a denied claim with denial reason."""
        result_dict = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="malfunction",
            status="denied",
            denial_reason="product_misuse",
        )

        self.assertEqual(result_dict["status"], "denied")
        self.assertEqual(result_dict["denialReason"], "product_misuse")

    def test_create_warranty_claim_with_notes(self):
        """Test creating claim with notes."""
        result_dict = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
            notes="Customer reported CPU overheating after 2 months of use",
        )

        self.assertEqual(result_dict["notes"], "Customer reported CPU overheating after 2 months of use")

    def test_create_warranty_claim_all_reasons(self):
        """Test all valid reason values."""
        for reason in VALID_REASONS:
            # Reset warranty_claim table
            self.data["warranty_claim"] = {}

            result_dict = CreateWarrantyClaim.invoke(
                self.data,
                product_id="prod1",
                order_id="order1",
                customer_id="cust1",
                reason=reason,
            )

            self.assertEqual(result_dict["reason"], reason)

    def test_create_warranty_claim_all_statuses(self):
        """Test all valid status values."""
        for status in VALID_STATUSES:
            # Reset warranty_claim table
            self.data["warranty_claim"] = {}

            result_dict = CreateWarrantyClaim.invoke(
                self.data,
                product_id="prod1",
                order_id="order1",
                customer_id="cust1",
                reason="defect",
                status=status,
            )

            self.assertEqual(result_dict["status"], status)

    def test_create_warranty_claim_all_denial_reasons(self):
        """Test all valid denial reason values."""
        for denial_reason in VALID_DENIAL_REASONS:
            # Reset warranty_claim table
            self.data["warranty_claim"] = {}

            result_dict = CreateWarrantyClaim.invoke(
                self.data,
                product_id="prod1",
                order_id="order1",
                customer_id="cust1",
                reason="defect",
                status="denied",
                denial_reason=denial_reason,
            )

            self.assertEqual(result_dict["denialReason"], denial_reason)

    def test_create_warranty_claim_invalid_reason(self):
        """Test creating claim with invalid reason."""
        result = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="invalid_reason",
        )
        self.assertIn("error", result)
        self.assertIn("Invalid reason", result["error"])

    def test_create_warranty_claim_invalid_status(self):
        """Test creating claim with invalid status."""
        result = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
            status="invalid_status",
        )
        self.assertIn("error", result)
        self.assertIn("Invalid status", result["error"])

    def test_create_warranty_claim_invalid_denial_reason(self):
        """Test creating claim with invalid denial reason."""
        result = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
            status="denied",
            denial_reason="invalid_denial",
        )
        self.assertIn("error", result)
        self.assertIn("Invalid denial_reason", result["error"])

    def test_create_warranty_claim_invalid_product(self):
        """Test creating claim for non-existent product."""
        result = CreateWarrantyClaim.invoke(
            self.data,
            product_id="nonexistent",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )
        self.assertIn("error", result)
        self.assertIn("nonexistent", result["error"])

    def test_create_warranty_claim_invalid_order(self):
        """Test creating claim for non-existent order."""
        result = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="nonexistent",
            customer_id="cust1",
            reason="defect",
        )
        self.assertIn("error", result)
        self.assertIn("nonexistent", result["error"])

    def test_create_warranty_claim_invalid_customer(self):
        """Test creating claim for non-existent customer."""
        result = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="nonexistent",
            reason="defect",
        )
        self.assertIn("error", result)
        self.assertIn("nonexistent", result["error"])

    def test_create_warranty_claim_mutates_data_in_place(self):
        """Test that the tool adds claim to data dict."""
        result_dict = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        # Check that claim was added to data
        self.assertIn("warranty_claim", self.data)
        self.assertIn(result_dict["id"], self.data["warranty_claim"])

    def test_create_warranty_claim_deterministic_id(self):
        """Test that the same inputs produce the same ID."""
        result1 = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        # Reset warranty_claim table
        self.data["warranty_claim"] = {}

        result2 = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        # Same inputs should produce same ID
        self.assertEqual(result1["id"], result2["id"])

    def test_create_warranty_claim_different_inputs_different_id(self):
        """Test that different inputs produce different IDs."""
        result1 = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        result2 = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="malfunction",  # Different reason
        )

        # Different reason should produce different ID
        self.assertNotEqual(result1["id"], result2["id"])

    def test_create_warranty_claim_uses_custom_timestamp(self):
        """Test that claim uses custom timestamp from data if provided."""
        self.data["__now"] = "2025-06-15T12:00:00Z"

        result_dict = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        self.assertEqual(result_dict["createdAt"], "2025-06-15T12:00:00Z")
        self.assertEqual(result_dict["updatedAt"], "2025-06-15T12:00:00Z")

    def test_create_warranty_claim_defaults_to_constant_timestamp(self):
        """Test that claim uses constant timestamp when not provided."""
        result_dict = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        self.assertEqual(result_dict["createdAt"], "1970-01-01T00:00:00Z")
        self.assertEqual(result_dict["updatedAt"], "1970-01-01T00:00:00Z")

    def test_create_warranty_claim_creates_table_if_missing(self):
        """Test that warranty_claim table is created if not present."""
        # Remove warranty_claim table if exists
        self.data.pop("warranty_claim", None)

        result_dict = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        self.assertIn("warranty_claim", self.data)
        self.assertIn(result_dict["id"], self.data["warranty_claim"])

    def test_create_warranty_claim_multiple_claims(self):
        """Test creating multiple warranty claims."""
        result1 = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        result2 = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prod2",
            order_id="order2",
            customer_id="cust2",
            reason="malfunction",
        )

        # Both claims should exist
        self.assertEqual(len(self.data["warranty_claim"]), 2)
        self.assertIn(result1["id"], self.data["warranty_claim"])
        self.assertIn(result2["id"], self.data["warranty_claim"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CreateWarrantyClaim.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "createWarrantyClaim")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])

        properties = info["function"]["parameters"]["properties"]
        self.assertIn("product_id", properties)
        self.assertIn("order_id", properties)
        self.assertIn("customer_id", properties)
        self.assertIn("reason", properties)
        self.assertIn("status", properties)
        self.assertIn("denial_reason", properties)
        self.assertIn("notes", properties)

        # Check enums are set correctly
        self.assertEqual(properties["reason"]["enum"], VALID_REASONS)
        self.assertEqual(properties["status"]["enum"], VALID_STATUSES)
        self.assertEqual(properties["denial_reason"]["enum"], VALID_DENIAL_REASONS)

        required = info["function"]["parameters"]["required"]
        self.assertIn("product_id", required)
        self.assertIn("order_id", required)
        self.assertIn("customer_id", required)
        self.assertIn("reason", required)
        self.assertNotIn("status", required)
        self.assertNotIn("denial_reason", required)
        self.assertNotIn("notes", required)

    def test_create_warranty_claim_rejects_prebuilt_products(self):
        """Test that prebuilt products cannot have warranty claims."""
        result = CreateWarrantyClaim.invoke(
            self.data,
            product_id="prebuilt1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        self.assertIn("error", result)
        self.assertIn("prebuilt", result["error"])
        self.assertIn("individual components", result["error"])

    def test_create_warranty_claim_rejects_workstation_products(self):
        """Test that workstation products cannot have warranty claims."""
        result = CreateWarrantyClaim.invoke(
            self.data,
            product_id="workstation1",
            order_id="order1",
            customer_id="cust1",
            reason="defect",
        )

        self.assertIn("error", result)
        self.assertIn("workstation", result["error"])
        self.assertIn("individual components", result["error"])

    def test_create_warranty_claim_all_build_categories_rejected(self):
        """Test that all build product categories are rejected."""
        for category in BUILD_PRODUCT_CATEGORIES:
            # Add a test product with this category
            test_product_id = f"test_{category}"
            self.data["product"][test_product_id] = {
                "id": test_product_id,
                "name": f"Test {category}",
                "category": category,
                "price": 1000.0,
            }

            result = CreateWarrantyClaim.invoke(
                self.data,
                product_id=test_product_id,
                order_id="order1",
                customer_id="cust1",
                reason="defect",
            )

            self.assertIn("error", result)
            self.assertIn(category, result["error"])
            self.assertIn("individual components", result["error"])


if __name__ == "__main__":
    unittest.main()
