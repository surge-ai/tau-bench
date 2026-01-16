import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_verify_customer import VerifyCustomer


class TestVerifyCustomer(unittest.TestCase):
    def setUp(self):
        """Set up test data with various customers."""
        self.data: Dict[str, Any] = {
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "(502) 555-1234",
                    "addresses": [
                        {
                            "label": "shipping",
                            "line1": "123 Main St",
                            "city": "Louisville",
                            "region": "KY",
                            "postalCode": "40204",
                            "country": "US"
                        }
                    ],
                },
                "customer2": {
                    "id": "customer2",
                    "name": "Jane Smith",
                    "email": "jane.smith@email.com",
                    "phone": "212-555-6789",
                    "addresses": [
                        {
                            "label": "billing",
                            "line1": "456 Park Ave",
                            "city": "New York",
                            "region": "NY",
                            "postalCode": "10001",
                            "country": "US"
                        },
                        {
                            "label": "shipping",
                            "line1": "789 Broadway",
                            "city": "Brooklyn",
                            "region": "NY",
                            "postalCode": "11201",
                            "country": "US"
                        }
                    ],
                },
                "customer3": {
                    "id": "customer3",
                    "name": "Bob Johnson",
                    "email": "bob@example.com",
                    "phone": "+1-555-123-4567",
                    "addresses": [
                        {
                            "label": "shipping",
                            "line1": "321 Elm St",
                            "city": "Toronto",
                            "region": "ON",
                            "postalCode": "M5H 2N2",  # Canadian postal code with space
                            "country": "CA"
                        }
                    ],
                },
                "customer4": {
                    "id": "customer4",
                    "name": "Alice Brown",
                    "email": "alice.brown@email.com",
                    "phone": None,  # No phone number
                    "addresses": [
                        {
                            "label": "shipping",
                            "line1": "555 Oak Ave",
                            "city": "Seattle",
                            "region": "WA",
                            "postalCode": "98101",
                            "country": "US"
                        }
                    ],
                },
            }
        }

    def test_verify_all_three_correct(self):
        """Test verification with all 3 identifiers correct."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="john@example.com",
            phone="(502) 555-1234",
            zip_code="40204",
        )

        self.assertTrue(result["validated"])
        self.assertEqual(result["match_count"], 3)
        self.assertIn("email", result["matches"])
        self.assertIn("phone", result["matches"])
        self.assertIn("zip_code", result["matches"])

    def test_verify_two_correct_email_phone(self):
        """Test verification with 2 correct identifiers (email and phone)."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="john@example.com",
            phone="5025551234",  # Different format
        )

        self.assertTrue(result["validated"])
        self.assertEqual(result["match_count"], 2)
        self.assertIn("email", result["matches"])
        self.assertIn("phone", result["matches"])

    def test_verify_two_correct_email_zip(self):
        """Test verification with 2 correct identifiers (email and zip)."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="john@example.com",
            zip_code="40204",
        )

        self.assertTrue(result["validated"])
        self.assertEqual(result["match_count"], 2)
        self.assertIn("email", result["matches"])
        self.assertIn("zip_code", result["matches"])

    def test_verify_two_correct_phone_zip(self):
        """Test verification with 2 correct identifiers (phone and zip)."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer2",
            phone="212-555-6789",
            zip_code="10001",
        )

        self.assertTrue(result["validated"])
        self.assertEqual(result["match_count"], 2)
        self.assertIn("phone", result["matches"])
        self.assertIn("zip_code", result["matches"])

    def test_verify_fails_with_one_wrong(self):
        """Test that verification fails if ANY identifier is wrong."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="john@example.com",  # Correct
            phone="555-555-5555",  # WRONG
            zip_code="40204",  # Correct
        )

        self.assertFalse(result["validated"])
        self.assertEqual(result["match_count"], 2)
        self.assertEqual(result["mismatch_count"], 1)
        self.assertIn("mismatches", result)

    def test_verify_fails_all_wrong(self):
        """Test that verification fails when all identifiers are wrong."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="wrong@email.com",
            phone="999-999-9999",
            zip_code="99999",
        )

        self.assertFalse(result["validated"])
        self.assertEqual(result["match_count"], 0)
        self.assertEqual(result["mismatch_count"], 3)

    def test_verify_error_only_one_identifier(self):
        """Test error when only 1 identifier provided."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="john@example.com",
        )

        self.assertIn("error", result)
        self.assertIn("At least 2", result["error"])
        self.assertEqual(result["actual_count"], 1)

    def test_verify_error_no_identifiers(self):
        """Test error when no identifiers provided."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
        )

        self.assertIn("error", result)
        self.assertIn("At least 2", result["error"])
        self.assertEqual(result["actual_count"], 0)

    def test_verify_customer_not_found(self):
        """Test error when customer doesn't exist."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="nonexistent",
            email="test@test.com",
            phone="555-555-5555",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_verify_email_case_insensitive(self):
        """Test that email comparison is case-insensitive."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="JOHN@EXAMPLE.COM",  # Uppercase
            phone="5025551234",
        )

        self.assertTrue(result["validated"])
        self.assertIn("email", result["matches"])

    def test_verify_phone_format_variations(self):
        """Test that phone normalization handles various formats."""
        # Customer2 has phone "212-555-6789"
        test_formats = [
            "2125556789",  # No formatting
            "(212) 555-6789",  # Parentheses
            "212.555.6789",  # Dots
            "+1-212-555-6789",  # Country code
        ]

        for phone_format in test_formats:
            result = VerifyCustomer.invoke(
                self.data,
                customer_id="customer2",
                email="jane.smith@email.com",
                phone=phone_format,
            )

            self.assertTrue(result["validated"], f"Failed for format: {phone_format}")
            self.assertIn("phone", result["matches"])

    def test_verify_zip_multiple_addresses(self):
        """Test that zip code is checked against all addresses."""
        # Customer2 has two addresses with different zips
        # Test with first address zip
        result1 = VerifyCustomer.invoke(
            self.data,
            customer_id="customer2",
            email="jane.smith@email.com",
            zip_code="10001",
        )
        self.assertTrue(result1["validated"])
        self.assertIn("zip_code", result1["matches"])

        # Test with second address zip
        result2 = VerifyCustomer.invoke(
            self.data,
            customer_id="customer2",
            email="jane.smith@email.com",
            zip_code="11201",
        )
        self.assertTrue(result2["validated"])
        self.assertIn("zip_code", result2["matches"])

    def test_verify_canadian_postal_code_with_space(self):
        """Test Canadian postal code with space."""
        # Customer3 has postal code "M5H 2N2"
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer3",
            email="bob@example.com",
            zip_code="M5H2N2",  # Without space
        )

        self.assertTrue(result["validated"])
        self.assertIn("zip_code", result["matches"])

    def test_verify_canadian_postal_code_case_insensitive(self):
        """Test that postal code comparison is case-insensitive."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer3",
            email="bob@example.com",
            zip_code="m5h 2n2",  # Lowercase
        )

        self.assertTrue(result["validated"])
        self.assertIn("zip_code", result["matches"])

    def test_verify_customer_no_phone(self):
        """Test verification for customer with no phone number."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer4",
            email="alice.brown@email.com",
            phone="555-555-5555",  # Won't match (customer has no phone)
            zip_code="98101",
        )

        # Should fail because phone doesn't match (customer has None)
        self.assertFalse(result["validated"])
        self.assertIn("phone", [m["field"] for m in result["mismatches"]])

    def test_verify_customer_only_email_and_zip(self):
        """Test verification without phone for customer with no phone."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer4",
            email="alice.brown@email.com",
            zip_code="98101",
        )

        self.assertTrue(result["validated"])
        self.assertEqual(result["match_count"], 2)

    def test_verify_returns_customer_name(self):
        """Test that successful verification returns customer name."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="john@example.com",
            phone="5025551234",
        )

        self.assertTrue(result["validated"])
        self.assertEqual(result["customer_name"], "John Doe")

    def test_verify_mismatch_details(self):
        """Test that mismatches include detailed information."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="wrong@email.com",
            phone="5025551234",  # Correct
        )

        self.assertFalse(result["validated"])
        self.assertEqual(len(result["mismatches"]), 1)

        mismatch = result["mismatches"][0]
        self.assertEqual(mismatch["field"], "email")
        self.assertEqual(mismatch["provided"], "wrong@email.com")
        self.assertIn("message", mismatch)

    def test_verify_response_structure_success(self):
        """Test the structure of a successful verification response."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="john@example.com",
            phone="5025551234",
        )

        self.assertIn("validated", result)
        self.assertIn("customer_id", result)
        self.assertIn("customer_name", result)
        self.assertIn("matches", result)
        self.assertIn("match_count", result)
        self.assertIn("message", result)
        self.assertNotIn("mismatches", result)

    def test_verify_response_structure_failure(self):
        """Test the structure of a failed verification response."""
        result = VerifyCustomer.invoke(
            self.data,
            customer_id="customer1",
            email="wrong@email.com",
            phone="5025551234",
        )

        self.assertIn("validated", result)
        self.assertIn("customer_id", result)
        self.assertIn("matches", result)
        self.assertIn("mismatches", result)
        self.assertIn("match_count", result)
        self.assertIn("mismatch_count", result)
        self.assertIn("message", result)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = VerifyCustomer.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "verify_customer")
        self.assertIn("description", info["function"])
        self.assertIn("at least 2", info["function"]["description"].lower())
        self.assertIn("parameters", info["function"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("email", info["function"]["parameters"]["properties"])
        self.assertIn("phone", info["function"]["parameters"]["properties"])
        self.assertIn("zip_code", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("customer_id", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
