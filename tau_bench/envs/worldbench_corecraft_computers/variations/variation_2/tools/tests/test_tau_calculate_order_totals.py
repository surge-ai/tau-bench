import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_calculate_order_totals import CalculateOrderTotals


class TestCalculateOrderTotals(unittest.TestCase):
    def setUp(self):
        """Set up test data with products and customers."""
        self.data: Dict[str, Any] = {
            "product": {
                "prod1": {
                    "id": "prod1",
                    "name": "Gaming Mouse",
                    "price": 59.99,
                    "category": "mouse",
                    # BUG: Product model has no "weight" field
                    # Line 40 tries to access product.get("weight", 0)
                },
                "prod2": {
                    "id": "prod2",
                    "name": "Mechanical Keyboard",
                    "price": 129.99,
                    "category": "keyboard",
                },
                "prod3": {
                    "id": "prod3",
                    "name": "27-inch Monitor",
                    "price": 299.99,
                    "category": "monitor",
                },
                "prod4": {
                    "id": "prod4",
                    "name": "USB Cable",
                    "price": 9.99,
                    "category": "cable",
                },
            },
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "loyaltyTier": "gold",
                },
                "customer2": {
                    "id": "customer2",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "loyaltyTier": "silver",
                },
                "customer3": {
                    "id": "customer3",
                    "name": "Bob Wilson",
                    "email": "bob@example.com",
                    "loyaltyTier": "platinum",
                },
                "customer4": {
                    "id": "customer4",
                    "name": "Alice Brown",
                    "email": "alice@example.com",
                    "loyaltyTier": "none",
                },
            },
        }

    def test_calculate_basic_order(self):
        """Test calculating totals for a simple order."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1", "prod2"],
        )

        # Subtotal: 59.99 + 129.99 = 189.98
        self.assertEqual(result["subtotal"], 189.98)
        self.assertEqual(len(result["items"]), 2)

        # No discounts
        self.assertEqual(result["discounts"]["total"], 0.0)
        self.assertEqual(result["discounted_subtotal"], 189.98)

        # Default 8% tax
        expected_tax = round(189.98 * 0.08, 2)
        self.assertEqual(result["tax"], expected_tax)
        self.assertEqual(result["tax_rate"], 0.08)

        # Default standard shipping: 9.99
        self.assertEqual(result["shipping"], 9.99)

        # Grand total
        expected_total = round(189.98 + expected_tax + 9.99, 2)
        self.assertEqual(result["grand_total"], expected_total)

        # BUG: total_weight is always 0 because Product model has no weight field
        self.assertEqual(result["total_weight"], 0.0)

    def test_calculate_with_quantities(self):
        """Test calculating totals with custom quantities."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1", "prod4"],
            quantities=[2, 3],
        )

        # Subtotal: (59.99 * 2) + (9.99 * 3) = 119.98 + 29.97 = 149.95
        self.assertEqual(result["subtotal"], 149.95)
        self.assertEqual(len(result["items"]), 2)

        # Check individual items
        prod1_item = next(i for i in result["items"] if i["product_id"] == "prod1")
        self.assertEqual(prod1_item["quantity"], 2)
        self.assertEqual(prod1_item["unit_price"], 59.99)
        self.assertEqual(prod1_item["item_total"], 119.98)

        prod4_item = next(i for i in result["items"] if i["product_id"] == "prod4")
        self.assertEqual(prod4_item["quantity"], 3)
        self.assertEqual(prod4_item["unit_price"], 9.99)
        self.assertEqual(prod4_item["item_total"], 29.97)

    def test_calculate_with_loyalty_discount(self):
        """Test loyalty tier discounts."""
        # Gold tier: 10% discount
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            customer_id="customer1",  # gold tier
        )

        subtotal = 59.99
        expected_loyalty_discount = round(subtotal * 0.10, 2)  # 10%
        self.assertEqual(result["discounts"]["loyalty"], expected_loyalty_discount)
        self.assertEqual(result["discounts"]["loyalty_tier"], "gold")

        # Silver tier: 5% discount
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            customer_id="customer2",  # silver tier
        )

        expected_loyalty_discount = round(subtotal * 0.05, 2)  # 5%
        self.assertEqual(result["discounts"]["loyalty"], expected_loyalty_discount)
        self.assertEqual(result["discounts"]["loyalty_tier"], "silver")

        # Platinum tier: 15% discount
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            customer_id="customer3",  # platinum tier
        )

        expected_loyalty_discount = round(subtotal * 0.15, 2)  # 15%
        self.assertEqual(result["discounts"]["loyalty"], expected_loyalty_discount)
        self.assertEqual(result["discounts"]["loyalty_tier"], "platinum")

        # None tier: no discount
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            customer_id="customer4",  # none tier
        )

        self.assertEqual(result["discounts"]["loyalty"], 0.0)
        self.assertEqual(result["discounts"]["loyalty_tier"], "none")

    def test_calculate_with_promo_code(self):
        """Test promo code discount (flat 10%)."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod2"],
            promo_code="SAVE10",
        )

        subtotal = 129.99
        expected_promo_discount = round(subtotal * 0.10, 2)  # 10%
        self.assertEqual(result["discounts"]["promo"], expected_promo_discount)
        self.assertEqual(result["discounts"]["promo_code"], "SAVE10")

    def test_calculate_with_combined_discounts(self):
        """Test that loyalty and promo discounts stack."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod3"],  # 299.99
            customer_id="customer1",  # gold: 10%
            promo_code="SAVE10",  # 10%
        )

        subtotal = 299.99
        loyalty_discount = round(subtotal * 0.10, 2)
        promo_discount = round(subtotal * 0.10, 2)
        total_discount = loyalty_discount + promo_discount

        self.assertEqual(result["discounts"]["loyalty"], loyalty_discount)
        self.assertEqual(result["discounts"]["promo"], promo_discount)
        self.assertEqual(result["discounts"]["total"], total_discount)

        expected_discounted_subtotal = round(subtotal - total_discount, 2)
        self.assertEqual(result["discounted_subtotal"], expected_discounted_subtotal)

    def test_calculate_with_custom_tax_rate(self):
        """Test custom tax rate."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            tax_rate=0.05,  # 5%
        )

        subtotal = 59.99
        expected_tax = round(subtotal * 0.05, 2)
        self.assertEqual(result["tax"], expected_tax)
        self.assertEqual(result["tax_rate"], 0.05)

    def test_calculate_with_different_shipping_methods(self):
        """Test different shipping methods."""
        product_ids = ["prod1"]

        # Standard: 9.99
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=product_ids,
            shipping_method="standard",
        )
        self.assertEqual(result["shipping"], 9.99)
        self.assertEqual(result["shipping_method"], "standard")

        # Express: 19.99
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=product_ids,
            shipping_method="express",
        )
        self.assertEqual(result["shipping"], 19.99)
        self.assertEqual(result["shipping_method"], "express")

        # Overnight: 39.99
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=product_ids,
            shipping_method="overnight",
        )
        self.assertEqual(result["shipping"], 39.99)
        self.assertEqual(result["shipping_method"], "overnight")

        # Free: 0.00
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=product_ids,
            shipping_method="free",
        )
        self.assertEqual(result["shipping"], 0.00)
        self.assertEqual(result["shipping_method"], "free")

    def test_calculate_weight_surcharge(self):
        """Test weight-based shipping surcharge."""
        # Add weight to products (even though this is a bug)
        self.data["product"]["heavy1"] = {
            "id": "heavy1",
            "name": "Heavy Item",
            "price": 100.0,
            "weight": 15.0,  # Over 10 lbs
        }

        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["heavy1"],
            shipping_method="standard",
        )

        # Base shipping: 9.99
        # Weight surcharge: (15 - 10) * 0.50 = 2.50
        # Total: 12.49
        expected_shipping = 9.99 + (15.0 - 10) * 0.50
        self.assertEqual(result["shipping"], expected_shipping)
        self.assertEqual(result["total_weight"], 15.0)

    def test_calculate_no_weight_surcharge_under_threshold(self):
        """Test no surcharge for items under 10 lbs."""
        # Add light products
        self.data["product"]["light1"] = {
            "id": "light1",
            "name": "Light Item",
            "price": 50.0,
            "weight": 5.0,
        }

        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["light1"],
            shipping_method="standard",
        )

        # No surcharge since weight <= 10
        self.assertEqual(result["shipping"], 9.99)
        self.assertEqual(result["total_weight"], 5.0)

    def test_calculate_default_quantities(self):
        """Test that quantities default to 1."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1", "prod2", "prod3"],
            # No quantities specified
        )

        # Should be 3 items with quantity 1 each
        self.assertEqual(len(result["items"]), 3)
        for item in result["items"]:
            self.assertEqual(item["quantity"], 1)

        # Subtotal: 59.99 + 129.99 + 299.99 = 489.97
        self.assertEqual(result["subtotal"], 489.97)

    def test_calculate_mismatched_quantities_length(self):
        """Test error when product_ids and quantities have different lengths."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1", "prod2"],
            quantities=[1],  # Only 1 quantity for 2 products
        )

        self.assertIn("error", result)
        self.assertIn("same length", result["error"])

    def test_calculate_nonexistent_product(self):
        """Test handling of non-existent products."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1", "nonexistent", "prod2"],
        )

        # Non-existent products are skipped
        self.assertEqual(len(result["items"]), 2)

        # Only prod1 and prod2 counted
        expected_subtotal = 59.99 + 129.99
        self.assertEqual(result["subtotal"], expected_subtotal)

    def test_calculate_nonexistent_customer(self):
        """Test with non-existent customer ID."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            customer_id="nonexistent",
        )

        # Should work but no loyalty discount
        self.assertEqual(result["subtotal"], 59.99)
        self.assertEqual(result["discounts"]["loyalty"], 0.0)
        self.assertIsNone(result["discounts"]["loyalty_tier"])

    def test_calculate_no_product_data(self):
        """Test when product table doesn't exist."""
        data_without_products = {}

        result = CalculateOrderTotals.invoke(
            data_without_products,
            product_ids=["prod1"],
        )

        self.assertIn("error", result)
        self.assertIn("Product data not available", result["error"])

    def test_calculate_invalid_product_table(self):
        """Test when product table is not a dict."""
        self.data["product"] = "not_a_dict"

        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
        )

        self.assertIn("error", result)
        self.assertIn("Product data not available", result["error"])

    def test_calculate_invalid_customer_table(self):
        """Test when customer table is not a dict."""
        self.data["customer"] = "not_a_dict"

        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            customer_id="customer1",
        )

        # Should still calculate but without loyalty discount
        self.assertEqual(result["subtotal"], 59.99)
        self.assertEqual(result["discounts"]["loyalty"], 0.0)

    def test_calculate_case_insensitive_shipping_method(self):
        """Test that shipping method is case-insensitive."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="EXPRESS",  # Uppercase
        )

        self.assertEqual(result["shipping"], 19.99)

    def test_calculate_unknown_shipping_method(self):
        """Test that unknown shipping method defaults to standard."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="unknown_method",
        )

        self.assertEqual(result["shipping"], 9.99)  # Default to standard

    def test_calculate_zero_price_product(self):
        """Test product with zero price."""
        self.data["product"]["free_item"] = {
            "id": "free_item",
            "name": "Free Item",
            "price": 0.0,
        }

        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["free_item"],
        )

        self.assertEqual(result["subtotal"], 0.0)
        self.assertEqual(result["discounted_subtotal"], 0.0)
        self.assertEqual(result["tax"], 0.0)
        # Shipping still applies
        self.assertEqual(result["shipping"], 9.99)
        self.assertEqual(result["grand_total"], 9.99)

    def test_calculate_rounding(self):
        """Test that all monetary values are rounded to 2 decimal places."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],  # 59.99
            customer_id="customer1",  # 10% discount
            promo_code="SAVE10",  # 10% discount
            tax_rate=0.08,
        )

        # All monetary values should have 2 decimal places
        self.assertEqual(len(str(result["subtotal"]).split(".")[-1]), 2)
        self.assertEqual(len(str(result["discounts"]["loyalty"]).split(".")[-1]), 2)
        self.assertEqual(len(str(result["discounts"]["promo"]).split(".")[-1]), 2)
        self.assertEqual(len(str(result["tax"]).split(".")[-1]), 2)
        self.assertEqual(len(str(result["shipping"]).split(".")[-1]), 2)

    def test_calculate_comprehensive(self):
        """Test comprehensive order with all features."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1", "prod2", "prod3"],
            quantities=[2, 1, 1],
            customer_id="customer3",  # platinum: 15%
            promo_code="SAVE10",  # 10%
            shipping_method="express",
            tax_rate=0.10,
        )

        # Subtotal: (59.99*2) + 129.99 + 299.99 = 549.96
        self.assertEqual(result["subtotal"], 549.96)

        # Loyalty discount: 549.96 * 0.15 = 82.49
        self.assertAlmostEqual(result["discounts"]["loyalty"], 82.49, places=2)

        # Promo discount: 549.96 * 0.10 = 54.99 (rounded)
        self.assertAlmostEqual(result["discounts"]["promo"], 55.0, places=2)

        # Discounted subtotal
        discounted = 549.96 - result["discounts"]["total"]
        self.assertAlmostEqual(result["discounted_subtotal"], discounted, places=2)

        # Tax: discounted * 0.10
        self.assertAlmostEqual(result["tax"], discounted * 0.10, places=2)

        # Shipping: express = 19.99 (no weight surcharge since weight=0)
        self.assertEqual(result["shipping"], 19.99)

        # Verify grand total
        expected_total = discounted + result["tax"] + result["shipping"]
        self.assertAlmostEqual(result["grand_total"], expected_total, places=2)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CalculateOrderTotals.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "calculate_order_totals")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("product_ids", info["function"]["parameters"]["properties"])
        self.assertIn("quantities", info["function"]["parameters"]["properties"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("promo_code", info["function"]["parameters"]["properties"])
        self.assertIn("shipping_method", info["function"]["parameters"]["properties"])
        self.assertIn("tax_rate", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("product_ids", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
