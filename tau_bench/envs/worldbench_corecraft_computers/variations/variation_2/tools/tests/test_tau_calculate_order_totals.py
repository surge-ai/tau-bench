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
            shipping_cost=9.99,
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

        # Shipping cost provided
        self.assertEqual(result["shipping"], 9.99)

        # Grand total
        expected_total = round(189.98 + expected_tax + 9.99, 2)
        self.assertEqual(result["grand_total"], expected_total)

    def test_calculate_with_quantities(self):
        """Test calculating totals with custom quantities."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1", "prod4"],
            quantities=[2, 3],
            shipping_cost=9.99,
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
            shipping_cost=9.99,
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
            shipping_cost=9.99,
        )

        expected_loyalty_discount = round(subtotal * 0.05, 2)  # 5%
        self.assertEqual(result["discounts"]["loyalty"], expected_loyalty_discount)
        self.assertEqual(result["discounts"]["loyalty_tier"], "silver")

        # Platinum tier: 15% discount
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            customer_id="customer3",  # platinum tier
            shipping_cost=9.99,
        )

        expected_loyalty_discount = round(subtotal * 0.15, 2)  # 15%
        self.assertEqual(result["discounts"]["loyalty"], expected_loyalty_discount)
        self.assertEqual(result["discounts"]["loyalty_tier"], "platinum")

        # None tier: no discount
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            customer_id="customer4",  # none tier
            shipping_cost=9.99,
        )

        self.assertEqual(result["discounts"]["loyalty"], 0.0)
        self.assertEqual(result["discounts"]["loyalty_tier"], "none")

    def test_calculate_with_promo_code(self):
        """Test promo code discount (flat 10%)."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod2"],
            promo_code="SAVE10",
            shipping_cost=9.99,
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
            shipping_cost=19.99,
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
            shipping_cost=9.99,
        )

        subtotal = 59.99
        expected_tax = round(subtotal * 0.05, 2)
        self.assertEqual(result["tax"], expected_tax)
        self.assertEqual(result["tax_rate"], 0.05)

    def test_calculate_with_different_shipping_costs(self):
        """Test different shipping costs."""
        product_ids = ["prod1"]

        # Standard shipping cost: 9.99
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=product_ids,
            shipping_cost=9.99,
        )
        self.assertEqual(result["shipping"], 9.99)

        # Express shipping cost: 19.99
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=product_ids,
            shipping_cost=19.99,
        )
        self.assertEqual(result["shipping"], 19.99)

        # Overnight shipping cost: 39.99
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=product_ids,
            shipping_cost=39.99,
        )
        self.assertEqual(result["shipping"], 39.99)

        # Free shipping: 0.00
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=product_ids,
            shipping_cost=0.00,
        )
        self.assertEqual(result["shipping"], 0.00)

    def test_calculate_with_destination_surcharge(self):
        """Test shipping with destination surcharge (from get_shipping_estimates)."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_cost=14.99,  # Standard 9.99 + destination surcharge 5.00
        )

        # Shipping should match provided cost
        self.assertEqual(result["shipping"], 14.99)

    def test_calculate_default_quantities(self):
        """Test that quantities default to 1."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1", "prod2", "prod3"],
            shipping_cost=9.99,
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
            shipping_cost=9.99,
        )

        # Non-existent products are skipped
        self.assertEqual(len(result["items"]), 2)

        # Only prod1 and prod2 counted
        self.assertAlmostEqual(result["subtotal"], 189.98, places=2)

    def test_calculate_nonexistent_customer(self):
        """Test with non-existent customer ID."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            customer_id="nonexistent",
            shipping_cost=9.99,
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
            shipping_cost=9.99,
        )

        # When product table doesn't exist, data.get("product", {}) returns {}
        # So products just aren't found and we get an empty result
        self.assertEqual(result["subtotal"], 0.0)
        self.assertEqual(len(result["items"]), 0)

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
            shipping_cost=9.99,
        )

        # Should still calculate but without loyalty discount
        self.assertEqual(result["subtotal"], 59.99)
        self.assertEqual(result["discounts"]["loyalty"], 0.0)

    def test_calculate_default_shipping_cost(self):
        """Test that shipping defaults to 0.0 if not provided."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1"],
            # No shipping_cost provided
        )

        self.assertEqual(result["shipping"], 0.0)

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
            shipping_cost=9.99,
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
            shipping_cost=9.99,
        )

        # All monetary values should have at most 2 decimal places
        # Check values are properly rounded
        self.assertIsInstance(result["subtotal"], (int, float))
        self.assertIsInstance(result["discounts"]["loyalty"], (int, float))
        self.assertIsInstance(result["discounts"]["promo"], (int, float))
        self.assertIsInstance(result["tax"], (int, float))
        self.assertIsInstance(result["shipping"], (int, float))

        # Verify no more than 2 decimal places by checking rounding equality
        self.assertEqual(result["subtotal"], round(result["subtotal"], 2))
        self.assertEqual(result["discounts"]["loyalty"], round(result["discounts"]["loyalty"], 2))
        self.assertEqual(result["discounts"]["promo"], round(result["discounts"]["promo"], 2))
        self.assertEqual(result["tax"], round(result["tax"], 2))
        self.assertEqual(result["shipping"], round(result["shipping"], 2))

    def test_calculate_comprehensive(self):
        """Test comprehensive order with all features."""
        result = CalculateOrderTotals.invoke(
            self.data,
            product_ids=["prod1", "prod2", "prod3"],
            quantities=[2, 1, 1],
            customer_id="customer3",  # platinum: 15%
            promo_code="SAVE10",  # 10%
            shipping_cost=19.99,  # Express shipping
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

        # Shipping: express = 19.99
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
        self.assertIn("get_shipping_estimates", info["function"]["description"])
        self.assertIn("parameters", info["function"])
        self.assertIn("product_ids", info["function"]["parameters"]["properties"])
        self.assertIn("quantities", info["function"]["parameters"]["properties"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("promo_code", info["function"]["parameters"]["properties"])
        self.assertIn("shipping_cost", info["function"]["parameters"]["properties"])
        self.assertIn("tax_rate", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("product_ids", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
