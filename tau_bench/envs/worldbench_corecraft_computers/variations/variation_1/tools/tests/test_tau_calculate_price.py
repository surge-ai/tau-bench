import json
import unittest
from typing import Dict, Any

from ..tau_calculate_price import CalculatePrice


class TestCalculatePrice(unittest.TestCase):
    def setUp(self):
        """Set up test data with sample products."""
        self.data: Dict[str, Any] = {
            "product": {
                "prod1": {
                    "id": "prod1",
                    "name": "Product 1",
                    "price": 100.0,
                    "weight": 1.5,
                    "inventory": json.dumps({"inStock": 10}),
                },
                "prod2": {
                    "id": "prod2",
                    "name": "Product 2",
                    "price": 50.0,
                    "weight": 0.8,
                    "inventory": json.dumps({"inStock": 5}),
                },
                "prod3": {
                    "id": "prod3",
                    "name": "Product 3",
                    "price": 200.0,
                    "weight": 2.0,
                    "inventory": json.dumps({"inStock": 20}),
                },
            }
        }

    def test_basic_calculation_single_product(self):
        """Test basic price calculation for a single product."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1"],
        )
        result_dict = result

        self.assertEqual(result_dict["subtotal"], 100.0)
        self.assertEqual(result_dict["discount"], 0.0)
        self.assertEqual(result_dict["shipping"], 9.99)
        self.assertEqual(result_dict["total"], 109.99)

    def test_basic_calculation_multiple_products(self):
        """Test price calculation for multiple products."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1", "prod2"],
            quantities=[2, 3],
        )
        result_dict = result

        # prod1: 100 * 2 = 200, prod2: 50 * 3 = 150, total = 350
        self.assertEqual(result_dict["subtotal"], 350.0)
        self.assertEqual(result_dict["discount"], 0.0)
        self.assertEqual(result_dict["shipping"], 9.99)
        self.assertEqual(result_dict["total"], 359.99)

    def test_default_quantities(self):
        """Test that quantities default to 1 if not provided."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1", "prod2", "prod3"],
        )
        result_dict = result

        # All quantities default to 1: 100 + 50 + 200 = 350
        self.assertEqual(result_dict["subtotal"], 350.0)

    def test_loyalty_discount_silver(self):
        """Test silver loyalty tier discount (5%)."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1"],
            quantities=[1],
            loyalty_tier="silver",
        )
        result_dict = result

        # 100 * 0.05 = 5 discount
        self.assertEqual(result_dict["subtotal"], 100.0)
        self.assertEqual(result_dict["discount"], 5.0)
        self.assertEqual(result_dict["shipping"], 9.99)
        self.assertEqual(result_dict["total"], 104.99)

    def test_loyalty_discount_gold(self):
        """Test gold loyalty tier discount (10%)."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1", "prod2"],
            quantities=[1, 1],
            loyalty_tier="gold",
        )
        result_dict = result

        # Subtotal: 150, discount: 150 * 0.1 = 15
        self.assertEqual(result_dict["subtotal"], 150.0)
        self.assertEqual(result_dict["discount"], 15.0)
        self.assertEqual(result_dict["shipping"], 9.99)
        self.assertEqual(result_dict["total"], 144.99)

    def test_loyalty_discount_platinum(self):
        """Test platinum loyalty tier discount (15%)."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod3"],
            quantities=[2],
            loyalty_tier="platinum",
        )
        result_dict = result

        # Subtotal: 400, discount: 400 * 0.15 = 60
        self.assertEqual(result_dict["subtotal"], 400.0)
        self.assertEqual(result_dict["discount"], 60.0)
        self.assertEqual(result_dict["shipping"], 9.99)
        self.assertEqual(result_dict["total"], 349.99)

    def test_loyalty_discount_invalid_tier(self):
        """Test that invalid loyalty tier raises ValueError."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1"],
            loyalty_tier="invalid",
        )
        self.assertIn("error", result)
        self.assertIn("Invalid loyalty_tier", result["error"])

    def test_loyalty_discount_case_sensitive(self):
        """Test that loyalty tier is case-sensitive (must match exactly)."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1"],
            loyalty_tier="GOLD",  # Should be "gold" (lowercase)
            )
        self.assertIn("error", result)
        self.assertIn("Invalid loyalty_tier", result["error"])

    def test_shipping_standard(self):
        """Test standard shipping rate."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_service="standard",
        )
        result_dict = result

        self.assertEqual(result_dict["shipping"], 9.99)

    def test_shipping_express(self):
        """Test express shipping rate."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_service="express",
        )
        result_dict = result

        self.assertEqual(result_dict["shipping"], 19.99)

    def test_shipping_overnight(self):
        """Test overnight shipping rate."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_service="overnight",
        )
        result_dict = result

        self.assertEqual(result_dict["shipping"], 39.99)

    def test_shipping_default(self):
        """Test that shipping defaults to standard if not provided."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1"],
        )
        result_dict = result

        self.assertEqual(result_dict["shipping"], 9.99)

    def test_shipping_invalid_service(self):
        """Test that invalid shipping service raises ValueError."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_service="invalid",
            )
        self.assertIn("error", result)
        self.assertIn("Invalid shipping_service", result["error"])

    def test_missing_product(self):
        """Test that missing products raise ValueError."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1", "nonexistent"],
            quantities=[1, 1],
            )
        self.assertIn("error", result)
        self.assertIn("nonexistent", result["error"])

    def test_quantity_mismatch_error(self):
        """Test that mismatched product_ids and quantities raises ValueError."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1", "prod2"],
            quantities=[1],  # Mismatch: 2 products but 1 quantity
            )
        self.assertIn("error", result)
        self.assertIn("must have same length", result["error"])

    def test_complex_scenario(self):
        """Test a complex scenario with all features."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=["prod1", "prod2", "prod3"],
            quantities=[2, 1, 3],
            loyalty_tier="platinum",
            shipping_service="express",
        )
        result_dict = result

        # Subtotal: (100*2) + (50*1) + (200*3) = 200 + 50 + 600 = 850
        # Discount: 850 * 0.15 = 127.5
        # Shipping: 19.99
        # Total: 850 - 127.5 + 19.99 = 742.49
        self.assertEqual(result_dict["subtotal"], 850.0)
        self.assertEqual(result_dict["discount"], 127.5)
        self.assertEqual(result_dict["shipping"], 19.99)
        self.assertEqual(result_dict["total"], 742.49)

    def test_empty_product_list(self):
        """Test with empty product list."""
        result = CalculatePrice.invoke(
            self.data,
            product_ids=[],
        )
        result_dict = result

        self.assertEqual(result_dict["subtotal"], 0.0)
        self.assertEqual(result_dict["discount"], 0.0)
        self.assertEqual(result_dict["shipping"], 9.99)
        self.assertEqual(result_dict["total"], 9.99)

    def test_rounding(self):
        """Test that prices are properly rounded to 2 decimal places."""
        # Create a product with a price that would cause rounding issues
        data_with_decimal = {
            "product": {
                "prod_decimal": {
                    "id": "prod_decimal",
                    "name": "Decimal Product",
                    "price": 33.333,
                    "weight": 1.0,
                    "inventory": json.dumps({"inStock": 10}),
                }
            }
        }

        result = CalculatePrice.invoke(
            data_with_decimal,
            product_ids=["prod_decimal"],
            quantities=[3],
        )
        result_dict = result

        # 33.333 * 3 = 99.999, should round to 100.0
        self.assertEqual(result_dict["subtotal"], 100.0)
        # Total should be properly rounded
        self.assertIsInstance(result_dict["total"], float)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CalculatePrice.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "calculate_price")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("product_ids", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("product_ids", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
