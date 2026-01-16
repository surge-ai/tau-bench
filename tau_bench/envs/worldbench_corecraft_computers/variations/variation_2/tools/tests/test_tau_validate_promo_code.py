import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_validate_promo_code import ValidatePromoCode


class TestValidatePromoCode(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        self.data: Dict[str, Any] = {}  # No data needed for this tool

    def test_validate_welcome10_code(self):
        """Test validating WELCOME10 promo code."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="WELCOME10",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["promo_code"], "WELCOME10")
        self.assertEqual(result["discount_type"], "percentage")
        self.assertEqual(result["discount_value"], 10.0)
        self.assertEqual(result["minimum_purchase"], 0.0)
        self.assertIsNone(result["max_discount"])
        self.assertIn("10% off", result["description"])

    def test_validate_save25_code(self):
        """Test validating SAVE25 promo code."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="SAVE25",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["promo_code"], "SAVE25")
        self.assertEqual(result["discount_type"], "fixed")
        self.assertEqual(result["discount_value"], 25.0)
        self.assertEqual(result["minimum_purchase"], 200.0)
        self.assertIsNone(result["max_discount"])
        self.assertIn("$25 off", result["description"])

    def test_validate_bulk20_code(self):
        """Test validating BULK20 promo code."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="BULK20",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["promo_code"], "BULK20")
        self.assertEqual(result["discount_type"], "percentage")
        self.assertEqual(result["discount_value"], 20.0)
        self.assertEqual(result["minimum_purchase"], 500.0)
        self.assertEqual(result["max_discount"], 100.0)
        self.assertIn("20% off", result["description"])

    def test_validate_freeship_code(self):
        """Test validating FREESHIP promo code."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="FREESHIP",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["promo_code"], "FREESHIP")
        self.assertEqual(result["discount_type"], "free_shipping")
        self.assertEqual(result["discount_value"], 0.0)
        self.assertEqual(result["minimum_purchase"], 0.0)
        self.assertIsNone(result["max_discount"])
        self.assertIn("Free shipping", result["description"])

    def test_validate_vip15_code(self):
        """Test validating VIP15 promo code."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="VIP15",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["promo_code"], "VIP15")
        self.assertEqual(result["discount_type"], "percentage")
        self.assertEqual(result["discount_value"], 15.0)
        self.assertEqual(result["minimum_purchase"], 0.0)
        self.assertEqual(result["max_discount"], 150.0)
        self.assertIn("15% off", result["description"])

    def test_validate_invalid_code(self):
        """Test validating an invalid promo code."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="INVALID123",
        )

        self.assertFalse(result["valid"])
        self.assertEqual(result["promo_code"], "INVALID123")
        self.assertIn("error", result)
        self.assertIn("not valid", result["error"])
        self.assertIn("active_promo_codes", result)
        self.assertIsInstance(result["active_promo_codes"], list)
        self.assertGreater(len(result["active_promo_codes"]), 0)

    def test_validate_case_insensitive_lowercase(self):
        """Test that promo code validation is case-insensitive (lowercase)."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="welcome10",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["promo_code"], "WELCOME10")

    def test_validate_case_insensitive_mixed(self):
        """Test that promo code validation is case-insensitive (mixed case)."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="WeLcOmE10",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["promo_code"], "WELCOME10")

    def test_validate_with_whitespace(self):
        """Test that promo code handles leading/trailing whitespace."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="  SAVE25  ",
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["promo_code"], "SAVE25")

    def test_validate_empty_string(self):
        """Test validating an empty promo code."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="",
        )

        self.assertFalse(result["valid"])
        self.assertIn("error", result)

    def test_validate_whitespace_only(self):
        """Test validating a whitespace-only promo code."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="   ",
        )

        self.assertFalse(result["valid"])
        self.assertIn("error", result)

    def test_invalid_code_shows_active_codes(self):
        """Test that invalid code error includes list of active codes."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="EXPIRED",
        )

        self.assertFalse(result["valid"])
        self.assertIn("active_promo_codes", result)

        # Check that known active codes are in the list
        active_codes = result["active_promo_codes"]
        self.assertIn("WELCOME10", active_codes)
        self.assertIn("SAVE25", active_codes)
        self.assertIn("BULK20", active_codes)
        self.assertIn("FREESHIP", active_codes)
        self.assertIn("VIP15", active_codes)

    def test_all_active_codes_validate(self):
        """Test that all documented active codes validate successfully."""
        active_codes = ["WELCOME10", "SAVE25", "BULK20", "FREESHIP", "VIP15"]

        for code in active_codes:
            result = ValidatePromoCode.invoke(self.data, promo_code=code)
            self.assertTrue(result["valid"], f"Code {code} should be valid")
            self.assertEqual(result["promo_code"], code)

    def test_valid_response_structure(self):
        """Test that valid response has correct structure."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="WELCOME10",
        )

        self.assertIn("valid", result)
        self.assertIn("promo_code", result)
        self.assertIn("description", result)
        self.assertIn("discount_type", result)
        self.assertIn("discount_value", result)
        self.assertIn("minimum_purchase", result)
        self.assertIn("max_discount", result)
        self.assertIn("message", result)

        self.assertIsInstance(result["valid"], bool)
        self.assertIsInstance(result["promo_code"], str)
        self.assertIsInstance(result["description"], str)
        self.assertIsInstance(result["discount_type"], str)
        self.assertIsInstance(result["discount_value"], (int, float))
        self.assertIsInstance(result["minimum_purchase"], (int, float))

    def test_invalid_response_structure(self):
        """Test that invalid response has correct structure."""
        result = ValidatePromoCode.invoke(
            self.data,
            promo_code="INVALID",
        )

        self.assertIn("valid", result)
        self.assertIn("promo_code", result)
        self.assertIn("error", result)
        self.assertIn("active_promo_codes", result)
        self.assertIn("message", result)

        self.assertIsInstance(result["valid"], bool)
        self.assertIsInstance(result["promo_code"], str)
        self.assertIsInstance(result["error"], str)
        self.assertIsInstance(result["active_promo_codes"], list)
        self.assertIsInstance(result["message"], str)

    def test_discount_types(self):
        """Test that different discount types are correctly represented."""
        # Percentage discount
        result_pct = ValidatePromoCode.invoke(self.data, promo_code="WELCOME10")
        self.assertEqual(result_pct["discount_type"], "percentage")

        # Fixed discount
        result_fixed = ValidatePromoCode.invoke(self.data, promo_code="SAVE25")
        self.assertEqual(result_fixed["discount_type"], "fixed")

        # Free shipping
        result_ship = ValidatePromoCode.invoke(self.data, promo_code="FREESHIP")
        self.assertEqual(result_ship["discount_type"], "free_shipping")

    def test_minimum_purchase_requirements(self):
        """Test that minimum purchase requirements are correctly set."""
        # No minimum
        result_no_min = ValidatePromoCode.invoke(self.data, promo_code="WELCOME10")
        self.assertEqual(result_no_min["minimum_purchase"], 0.0)

        # $200 minimum
        result_200 = ValidatePromoCode.invoke(self.data, promo_code="SAVE25")
        self.assertEqual(result_200["minimum_purchase"], 200.0)

        # $500 minimum
        result_500 = ValidatePromoCode.invoke(self.data, promo_code="BULK20")
        self.assertEqual(result_500["minimum_purchase"], 500.0)

    def test_max_discount_caps(self):
        """Test that max discount caps are correctly set."""
        # No cap
        result_no_cap = ValidatePromoCode.invoke(self.data, promo_code="WELCOME10")
        self.assertIsNone(result_no_cap["max_discount"])

        # $100 cap
        result_capped = ValidatePromoCode.invoke(self.data, promo_code="BULK20")
        self.assertEqual(result_capped["max_discount"], 100.0)

        # $150 cap
        result_vip = ValidatePromoCode.invoke(self.data, promo_code="VIP15")
        self.assertEqual(result_vip["max_discount"], 150.0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = ValidatePromoCode.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "validate_promo_code")
        self.assertIn("description", info["function"])
        self.assertIn("promo", info["function"]["description"].lower())
        self.assertIn("parameters", info["function"])
        self.assertIn("promo_code", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("promo_code", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
