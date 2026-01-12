import json
import unittest
from typing import Dict, Any
from datetime import datetime, timedelta, timezone

from ..tau_check_warranty_status import CheckWarrantyStatus


class TestCheckWarrantyStatus(unittest.TestCase):
    def setUp(self):
        """Set up test data with orders and products."""
        self.base_date = datetime(2025, 9, 8, 0, 0, 0, tzinfo=timezone.utc)

        self.data: Dict[str, Any] = {
            "order": {
                "order1": {
                    "id": "order1",
                    "createdAt": "2024-09-08T00:00:00Z",  # Exactly 1 year ago
                    "status": "completed",
                    "lineItems": json.dumps([
                        {"productId": "prod1", "quantity": 1, "price": 100.0}
                    ])
                },
                "order2": {
                    "id": "order2",
                    "createdAt": "2024-06-08T00:00:00Z",  # 15 months ago (expired)
                    "status": "completed",
                    "lineItems": json.dumps([
                        {"productId": "prod2", "quantity": 2, "price": 200.0}
                    ])
                },
                "order3": {
                    "id": "order3",
                    "createdAt": "2025-08-08T00:00:00Z",  # 1 month ago (still under warranty)
                    "status": "completed",
                    "lineItems": json.dumps([
                        {"productId": "prod3", "quantity": 1, "price": 150.0}
                    ])
                },
                "order4": {
                    "id": "order4",
                    "createdAt": "2024-09-09T00:00:00Z",  # 1 day before 1 year
                    "status": "completed",
                    "lineItems": json.dumps([
                        {"productId": "prod4", "quantity": 1, "price": 120.0}
                    ])
                },
            },
            "product": {
                "prod1": {
                    "id": "prod1",
                    "name": "Product 1",
                    "price": 100.0,
                    "warrantyMonths": 12,  # Standard warranty
                },
                "prod2": {
                    "id": "prod2",
                    "name": "Product 2",
                    "price": 200.0,
                    "warrantyMonths": 12,
                },
                "prod3": {
                    "id": "prod3",
                    "name": "Product 3",
                    "price": 150.0,
                    "warrantyMonths": 24,  # Extended warranty
                },
                "prod4": {
                    "id": "prod4",
                    "name": "Product 4",
                    "price": 120.0,
                    "warrantyMonths": 12,
                },
                "prod5": {
                    "id": "prod5",
                    "name": "Product 5",
                    "price": 300.0,
                    "warrantyMonths": 6,  # Short warranty
                },
            }
        }

    def test_check_warranty_by_order_id_valid(self):
        """Test checking warranty by order_id when warranty is still valid."""
        result = CheckWarrantyStatus.invoke(
            self.data,
            order_id="order3",  # Purchased 1 month ago
        )
        result_dict = json.loads(result)

        self.assertTrue(result_dict["is_under_warranty"])
        self.assertIn("warranty_end_date", result_dict)
        self.assertGreater(result_dict["days_remaining"], 0)

    def test_check_warranty_by_order_id_expired(self):
        """Test checking warranty by order_id when warranty has expired."""
        result = CheckWarrantyStatus.invoke(
            self.data,
            order_id="order2",  # Purchased 15 months ago
        )
        result_dict = json.loads(result)

        self.assertFalse(result_dict["is_under_warranty"])
        self.assertIn("warranty_end_date", result_dict)
        self.assertEqual(result_dict["days_remaining"], 0)

    def test_check_warranty_by_product_id_with_purchase_date(self):
        """Test checking warranty by product_id with explicit purchase date."""
        # Purchase date 6 months ago, product has 12 month warranty
        purchase_date = (self.base_date - timedelta(days=180)).isoformat().replace('+00:00', 'Z')

        result = CheckWarrantyStatus.invoke(
            self.data,
            product_id="prod1",
            purchase_date=purchase_date,
        )
        result_dict = json.loads(result)

        self.assertTrue(result_dict["is_under_warranty"])
        self.assertGreater(result_dict["days_remaining"], 0)

    def test_check_warranty_by_product_id_without_purchase_date(self):
        """Test checking warranty by product_id without purchase date (uses default)."""
        result = CheckWarrantyStatus.invoke(
            self.data,
            product_id="prod1",
        )
        result_dict = json.loads(result)

        # Uses default current date, so warranty starts today
        self.assertTrue(result_dict["is_under_warranty"])
        self.assertIn("warranty_end_date", result_dict)

    def test_check_warranty_nonexistent_order(self):
        """Test checking warranty for non-existent order."""
        result = CheckWarrantyStatus.invoke(
            self.data,
            order_id="nonexistent_order",
        )
        result_dict = json.loads(result)

        self.assertFalse(result_dict["is_under_warranty"])

    def test_check_warranty_nonexistent_product(self):
        """Test checking warranty for non-existent product."""
        result = CheckWarrantyStatus.invoke(
            self.data,
            product_id="nonexistent_product",
        )
        result_dict = json.loads(result)

        self.assertFalse(result_dict["is_under_warranty"])

    def test_check_warranty_no_order_or_product_id(self):
        """Test that providing neither order_id nor product_id raises an error."""
        with self.assertRaises(ValueError):
            CheckWarrantyStatus.invoke(
                self.data,
            )

    def test_check_warranty_with_custom_current_date(self):
        """Test checking warranty with a custom current_time in data."""
        # Order purchased 1 year ago
        # But we set current_time to 6 months ago, so warranty should still be valid
        custom_current = (self.base_date - timedelta(days=180)).isoformat().replace('+00:00', 'Z')

        # The tool reads current_time from data, not as a parameter
        self.data["current_time"] = custom_current

        result = CheckWarrantyStatus.invoke(
            self.data,
            order_id="order1",  # Purchased 1 year ago
        )
        result_dict = json.loads(result)

        # From 6 months ago perspective, warranty was still valid
        self.assertTrue(result_dict["is_under_warranty"])
        self.assertGreater(result_dict["days_remaining"], 0)

    def test_check_warranty_product_default_warranty(self):
        """Test that product without warrantyMonths uses default 12 months."""
        data_without_warranty = {
            "product": {
                "prod_no_warranty": {
                    "id": "prod_no_warranty",
                    "name": "Product No Warranty",
                    "price": 100.0,
                    # No warrantyMonths field - should default to 12
                }
            }
        }

        # Purchase date 6 months ago
        purchase_date = (self.base_date - timedelta(days=180)).isoformat().replace('+00:00', 'Z')

        result = CheckWarrantyStatus.invoke(
            data_without_warranty,
            product_id="prod_no_warranty",
            purchase_date=purchase_date,
        )
        result_dict = json.loads(result)

        # Should use default 12 month warranty
        self.assertTrue(result_dict["is_under_warranty"])
        self.assertGreater(result_dict["days_remaining"], 0)

    def test_check_warranty_warranty_end_date_format(self):
        """Test that warranty_end_date is in correct format (YYYY-MM-DD)."""
        result = CheckWarrantyStatus.invoke(
            self.data,
            order_id="order3",
        )
        result_dict = json.loads(result)

        self.assertIn("warranty_end_date", result_dict)
        warranty_end = result_dict["warranty_end_date"]
        # Should be in YYYY-MM-DD format
        self.assertRegex(warranty_end, r'^\d{4}-\d{2}-\d{2}$')
        # Should be a valid date
        datetime.fromisoformat(warranty_end)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CheckWarrantyStatus.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "checkWarrantyStatus")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("order_id", info["function"]["parameters"]["properties"])
        self.assertIn("product_id", info["function"]["parameters"]["properties"])
        self.assertIn("purchase_date", info["function"]["parameters"]["properties"])


if __name__ == "__main__":
    unittest.main()
