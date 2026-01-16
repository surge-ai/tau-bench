import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_get_shipping_estimates import GetShippingEstimates


class TestGetShippingEstimates(unittest.TestCase):
    def setUp(self):
        """Set up test data with products."""
        self.data: Dict[str, Any] = {
            "__now": "2025-01-15T10:00:00Z",
            "product": {
                "prod1": {
                    "id": "prod1",
                    "name": "Gaming Mouse",
                    "price": 59.99,
                    # BUG: Product model has no "weight" field
                    # Line 30 tries to access product.get("weight", 0)
                },
                "prod2": {
                    "id": "prod2",
                    "name": "Mechanical Keyboard",
                    "price": 129.99,
                },
                "prod3": {
                    "id": "prod3",
                    "name": "27-inch Monitor",
                    "price": 299.99,
                },
            },
        }

    def test_get_shipping_estimate_standard(self):
        """Test getting shipping estimate with standard shipping."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="standard",
        )

        self.assertEqual(result["shipping_method"], "standard")
        self.assertEqual(result["cost_breakdown"]["base_rate"], 9.99)

        # BUG: total_weight is always 0 because Product has no weight field
        self.assertEqual(result["weight"]["total_weight_lbs"], 0.0)
        self.assertEqual(result["cost_breakdown"]["weight_surcharge"], 0.0)
        self.assertEqual(result["cost_breakdown"]["total_cost"], 9.99)

        # Timing: 1 day processing + 7 days transit = 8 days total
        self.assertEqual(result["timing"]["processing_days"], 1)
        self.assertEqual(result["timing"]["transit_days"], 7)
        self.assertEqual(result["timing"]["total_days"], 8)

    def test_get_shipping_estimate_express(self):
        """Test express shipping method."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="express",
        )

        self.assertEqual(result["shipping_method"], "express")
        self.assertEqual(result["cost_breakdown"]["base_rate"], 19.99)
        self.assertEqual(result["timing"]["transit_days"], 3)
        self.assertEqual(result["timing"]["total_days"], 4)

    def test_get_shipping_estimate_overnight(self):
        """Test overnight shipping method."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="overnight",
        )

        self.assertEqual(result["shipping_method"], "overnight")
        self.assertEqual(result["cost_breakdown"]["base_rate"], 39.99)
        self.assertEqual(result["timing"]["transit_days"], 1)
        self.assertEqual(result["timing"]["total_days"], 2)

    def test_get_shipping_estimate_two_day(self):
        """Test two-day shipping method."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="two_day",
        )

        self.assertEqual(result["shipping_method"], "two_day")
        self.assertEqual(result["cost_breakdown"]["base_rate"], 29.99)
        self.assertEqual(result["timing"]["transit_days"], 2)
        self.assertEqual(result["timing"]["total_days"], 3)

    def test_get_shipping_estimate_free(self):
        """Test free shipping method."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="free",
        )

        self.assertEqual(result["shipping_method"], "free")
        self.assertEqual(result["cost_breakdown"]["base_rate"], 0.00)
        self.assertEqual(result["timing"]["transit_days"], 10)
        self.assertEqual(result["timing"]["total_days"], 11)

    def test_get_shipping_estimate_multiple_products(self):
        """Test shipping estimate with multiple products."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1", "prod2", "prod3"],
            shipping_method="standard",
        )

        self.assertEqual(len(result["products"]), 3)
        product_ids = {p["product_id"] for p in result["products"]}
        self.assertIn("prod1", product_ids)
        self.assertIn("prod2", product_ids)
        self.assertIn("prod3", product_ids)

        # BUG: total_weight still 0 because Product has no weight
        self.assertEqual(result["weight"]["total_weight_lbs"], 0.0)

    def test_get_shipping_estimate_with_weight_surcharge(self):
        """Test weight surcharge when weight > 10 lbs."""
        # Add products with weight (even though this is a bug)
        self.data["product"]["heavy1"] = {
            "id": "heavy1",
            "name": "Heavy Item",
            "price": 100.0,
            "weight": 15.0,  # Over 10 lbs
        }

        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["heavy1"],
            shipping_method="standard",
        )

        self.assertEqual(result["weight"]["total_weight_lbs"], 15.0)
        # Weight surcharge: (15 - 10) * 0.50 = 2.50
        self.assertEqual(result["cost_breakdown"]["weight_surcharge"], 2.50)
        # Total: 9.99 + 2.50 = 12.49
        self.assertEqual(result["cost_breakdown"]["total_cost"], 12.49)

    def test_get_shipping_estimate_no_weight_surcharge(self):
        """Test no surcharge when weight <= 10 lbs."""
        self.data["product"]["light1"] = {
            "id": "light1",
            "name": "Light Item",
            "price": 50.0,
            "weight": 5.0,
        }

        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["light1"],
            shipping_method="standard",
        )

        self.assertEqual(result["weight"]["total_weight_lbs"], 5.0)
        self.assertEqual(result["cost_breakdown"]["weight_surcharge"], 0.0)
        self.assertEqual(result["cost_breakdown"]["total_cost"], 9.99)

    def test_get_shipping_estimate_oversized(self):
        """Test oversized flag when weight > 50 lbs."""
        self.data["product"]["oversized"] = {
            "id": "oversized",
            "name": "Very Heavy Item",
            "price": 500.0,
            "weight": 60.0,
        }

        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["oversized"],
            shipping_method="standard",
        )

        self.assertEqual(result["weight"]["total_weight_lbs"], 60.0)
        self.assertTrue(result["weight"]["is_oversized"])

        # Weight surcharge: (60 - 10) * 0.50 = 25.00
        self.assertEqual(result["cost_breakdown"]["weight_surcharge"], 25.0)

    def test_get_shipping_estimate_not_oversized(self):
        """Test oversized flag is False when weight <= 50 lbs."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="standard",
        )

        self.assertFalse(result["weight"]["is_oversized"])

    def test_get_shipping_estimate_with_destination_zip(self):
        """Test destination surcharge."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="standard",
            destination_zip="90210",  # Starts with 9 (West Coast)
        )

        self.assertEqual(result["destination_zip"], "90210")
        # West Coast surcharge: $5.00
        self.assertEqual(result["cost_breakdown"]["destination_surcharge"], 5.0)
        # Total: 9.99 + 0 (weight) + 5.00 (destination) = 14.99
        self.assertEqual(result["cost_breakdown"]["total_cost"], 14.99)

    def test_get_shipping_estimate_no_destination_surcharge(self):
        """Test no destination surcharge for non-West Coast."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="standard",
            destination_zip="12345",  # Doesn't start with 9
        )

        self.assertEqual(result["destination_zip"], "12345")
        self.assertEqual(result["cost_breakdown"]["destination_surcharge"], 0.0)

    def test_get_shipping_estimate_without_destination_zip(self):
        """Test without destination zip."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="standard",
        )

        self.assertIsNone(result["destination_zip"])
        self.assertEqual(result["cost_breakdown"]["destination_surcharge"], 0.0)

    def test_get_shipping_estimate_default_method(self):
        """Test that shipping method defaults to standard."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
        )

        self.assertEqual(result["shipping_method"], "standard")

    def test_get_shipping_estimate_unknown_method(self):
        """Test that unknown method defaults to standard."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="unknown_method",
        )

        self.assertEqual(result["shipping_method"], "standard")
        self.assertEqual(result["cost_breakdown"]["base_rate"], 9.99)

    def test_get_shipping_estimate_case_insensitive_method(self):
        """Test that shipping method is case-insensitive."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="EXPRESS",  # Uppercase
        )

        self.assertEqual(result["shipping_method"], "express")
        self.assertEqual(result["cost_breakdown"]["base_rate"], 19.99)

    def test_get_shipping_estimate_nonexistent_product(self):
        """Test with non-existent product."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["nonexistent"],
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_get_shipping_estimate_some_nonexistent_products(self):
        """Test with mix of existing and non-existing products."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1", "nonexistent"],
        )

        # Should error on first nonexistent product
        self.assertIn("error", result)

    def test_get_shipping_estimate_no_product_data(self):
        """Test when product table doesn't exist."""
        data_without_products = {}

        result = GetShippingEstimates.invoke(
            data_without_products,
            product_ids=["prod1"],
        )

        self.assertIn("error", result)
        self.assertIn("Product data not available", result["error"])

    def test_get_shipping_estimate_invalid_product_table(self):
        """Test when product table is not a dict."""
        self.data["product"] = "not_a_dict"

        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
        )

        self.assertIn("error", result)
        self.assertIn("Product data not available", result["error"])

    def test_get_shipping_estimate_delivery_dates(self):
        """Test delivery date calculations."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="express",
        )

        # Ship date: current + 1 day
        self.assertEqual(result["timing"]["estimated_ship_date"], "2025-01-16")

        # Delivery date: current + 1 (processing) + 3 (transit) = 4 days
        self.assertEqual(result["timing"]["estimated_delivery_date"], "2025-01-19")

    def test_get_shipping_estimate_uses_custom_timestamp(self):
        """Test that custom timestamp is used for date calculations."""
        self.data["__now"] = "2025-12-25T00:00:00Z"

        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="overnight",
        )

        # Ship date: 2025-12-25 + 1 day = 2025-12-26
        self.assertEqual(result["timing"]["estimated_ship_date"], "2025-12-26")

        # Delivery date: 2025-12-25 + 2 days total = 2025-12-27
        self.assertEqual(result["timing"]["estimated_delivery_date"], "2025-12-27")

    def test_get_shipping_estimate_comprehensive(self):
        """Test comprehensive shipping estimate with all features."""
        self.data["product"]["heavy1"] = {
            "id": "heavy1",
            "name": "Heavy Item",
            "price": 100.0,
            "weight": 20.0,
        }

        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["heavy1"],
            shipping_method="express",
            destination_zip="94102",  # West Coast
        )

        # Express base: 19.99
        self.assertEqual(result["cost_breakdown"]["base_rate"], 19.99)

        # Weight surcharge: (20 - 10) * 0.50 = 5.00
        self.assertEqual(result["cost_breakdown"]["weight_surcharge"], 5.0)

        # Destination surcharge: 5.00 (West Coast)
        self.assertEqual(result["cost_breakdown"]["destination_surcharge"], 5.0)

        # Total: 19.99 + 5.00 + 5.00 = 29.99
        self.assertEqual(result["cost_breakdown"]["total_cost"], 29.99)

        # Weight info
        self.assertEqual(result["weight"]["total_weight_lbs"], 20.0)
        self.assertFalse(result["weight"]["is_oversized"])

    def test_get_shipping_estimate_response_structure(self):
        """Test that response has correct structure."""
        result = GetShippingEstimates.invoke(
            self.data,
            product_ids=["prod1"],
            shipping_method="standard",
            destination_zip="12345",
        )

        # Verify structure
        self.assertIn("shipping_method", result)
        self.assertIn("products", result)
        self.assertIn("weight", result)
        self.assertIn("cost_breakdown", result)
        self.assertIn("timing", result)
        self.assertIn("destination_zip", result)

        # Verify nested structures
        self.assertIn("total_weight_lbs", result["weight"])
        self.assertIn("is_oversized", result["weight"])

        self.assertIn("base_rate", result["cost_breakdown"])
        self.assertIn("weight_surcharge", result["cost_breakdown"])
        self.assertIn("destination_surcharge", result["cost_breakdown"])
        self.assertIn("total_cost", result["cost_breakdown"])

        self.assertIn("processing_days", result["timing"])
        self.assertIn("transit_days", result["timing"])
        self.assertIn("total_days", result["timing"])
        self.assertIn("estimated_ship_date", result["timing"])
        self.assertIn("estimated_delivery_date", result["timing"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetShippingEstimates.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "get_shipping_estimates")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("product_ids", info["function"]["parameters"]["properties"])
        self.assertIn("destination_zip", info["function"]["parameters"]["properties"])
        self.assertIn("shipping_method", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("product_ids", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
