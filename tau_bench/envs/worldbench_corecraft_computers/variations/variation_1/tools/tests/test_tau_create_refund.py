import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
# We're in tests/ subdirectory, so go up one level to tools/
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

# Import dependencies first
from tau_bench.envs.tool import Tool

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_create_refund import CreateRefund


class TestCreateRefund(unittest.TestCase):
    def setUp(self):
        """Set up test data with payments."""
        self.data: Dict[str, Any] = {
            "Payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 100.0,
                    "currency": "USD",
                    "status": "captured",
                    "method": "card",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order2",
                    "amount": 250.50,
                    "currency": "USD",
                    "status": "captured",
                    "method": "card",
                },
            }
        }

    def test_create_refund_basic(self):
        """Test creating a basic refund."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        
        # Check that refund was created with correct fields
        self.assertIn("id", result_dict)
        self.assertTrue(result_dict["id"].startswith("refund_"))
        self.assertEqual(result_dict["type"], "refund")
        self.assertEqual(result_dict["paymentId"], "payment1")
        self.assertEqual(result_dict["amount"], 100.0)
        self.assertEqual(result_dict["currency"], "USD")
        self.assertEqual(result_dict["reason"], "customer_remorse")
        self.assertIsNone(result_dict["notes"])
        self.assertEqual(result_dict["status"], "pending")
        self.assertEqual(result_dict["lines"], [])
        self.assertIsNone(result_dict["processedAt"])
        self.assertIn("createdAt", result_dict)
        
        # Check that refund was added to data
        self.assertIn("Refund", self.data)
        self.assertEqual(len(self.data["Refund"]), 1)
        self.assertEqual(self.data["Refund"][0]["paymentId"], "payment1")

    def test_create_refund_with_notes(self):
        """Test creating a refund with notes."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=50.0,
            currency="USD",
            reason="defective",
            notes="Item was damaged upon arrival",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["notes"], "Item was damaged upon arrival")
        self.assertEqual(result_dict["reason"], "defective")
        self.assertEqual(result_dict["amount"], 50.0)

    def test_create_refund_with_status(self):
        """Test creating a refund with custom status."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="incompatible",
            status="approved",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["status"], "approved")

    def test_create_refund_with_lines(self):
        """Test creating a refund with line items."""
        lines = [
            {"sku": "PROD-001", "qty": 1, "amount": 75.0},
            {"sku": "PROD-002", "qty": 2, "amount": 25.0},
        ]
        
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="shipping_issue",
            lines=lines,
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["lines"], lines)
        self.assertEqual(len(result_dict["lines"]), 2)

    def test_create_refund_all_fields(self):
        """Test creating a refund with all fields populated."""
        lines = [{"sku": "PROD-001", "qty": 1, "amount": 100.0}]
        
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="other",
            notes="Customer requested refund",
            status="processing",
            lines=lines,
        )
        result_dict = json.loads(result)
        
        # Verify all fields
        self.assertIn("id", result_dict)
        self.assertEqual(result_dict["type"], "refund")
        self.assertEqual(result_dict["paymentId"], "payment1")
        self.assertEqual(result_dict["amount"], 100.0)
        self.assertEqual(result_dict["currency"], "USD")
        self.assertEqual(result_dict["reason"], "other")
        self.assertEqual(result_dict["notes"], "Customer requested refund")
        self.assertEqual(result_dict["status"], "processing")
        self.assertEqual(result_dict["lines"], lines)
        self.assertIsNone(result_dict["processedAt"])

    def test_create_refund_nonexistent_payment(self):
        """Test that creating refund for non-existent payment raises error."""
        with self.assertRaises(ValueError) as context:
            CreateRefund.invoke(
                self.data,
                payment_id="nonexistent",
                amount=100.0,
                currency="USD",
                reason="customer_remorse",
            )
        
        self.assertIn("not found", str(context.exception))

    def test_create_refund_payment_in_list_format(self):
        """Test that payments can be in list format."""
        data_list = {
            "Payment": [
                {
                    "id": "payment_list",
                    "orderId": "order1",
                    "amount": 100.0,
                    "currency": "USD",
                }
            ]
        }
        
        result = CreateRefund.invoke(
            data_list,
            payment_id="payment_list",
            amount=50.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["paymentId"], "payment_list")
        self.assertIn("Refund", data_list)
        self.assertEqual(len(data_list["Refund"]), 1)

    def test_create_refund_different_payment_key_names(self):
        """Test that payments can be found under different key names."""
        # Test with lowercase key
        data_lower = {
            "payment": {
                "payment_lower": {
                    "id": "payment_lower",
                    "amount": 100.0,
                    "currency": "USD",
                }
            }
        }
        
        result = CreateRefund.invoke(
            data_lower,
            payment_id="payment_lower",
            amount=50.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        self.assertEqual(result_dict["paymentId"], "payment_lower")
        
        # Test with payments (plural)
        data_plural = {
            "payments": {
                "payment_plural": {
                    "id": "payment_plural",
                    "amount": 100.0,
                    "currency": "USD",
                }
            }
        }
        
        result = CreateRefund.invoke(
            data_plural,
            payment_id="payment_plural",
            amount=50.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        self.assertEqual(result_dict["paymentId"], "payment_plural")

    def test_create_refund_uses_custom_timestamp(self):
        """Test that refund uses custom timestamp from data if available."""
        self.data["__now"] = "2025-09-15T12:30:00Z"
        
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["createdAt"], "2025-09-15T12:30:00Z")

    def test_create_refund_defaults_to_constant_timestamp(self):
        """Test that refund defaults to constant timestamp if none provided."""
        # Remove any timestamp keys
        self.data.pop("__now", None)
        self.data.pop("now", None)
        self.data.pop("current_time", None)
        self.data.pop("currentTime", None)
        
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        
        # Should default to constant
        self.assertEqual(result_dict["createdAt"], "1970-01-01T00:00:00Z")

    def test_create_refund_creates_lowercase_alias(self):
        """Test that refund is also added to lowercase alias if present."""
        self.data["refunds"] = []
        
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        
        # Should be in both Refund and refunds
        self.assertEqual(len(self.data["Refund"]), 1)
        self.assertEqual(len(self.data["refunds"]), 1)
        self.assertEqual(self.data["Refund"][0]["id"], result_dict["id"])
        self.assertEqual(self.data["refunds"][0]["id"], result_dict["id"])

    def test_create_refund_creates_singular_lowercase_alias(self):
        """Test that refund is added to singular lowercase alias if present."""
        self.data["refund"] = []
        
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        
        # Should be in both Refund and refund
        self.assertEqual(len(self.data["Refund"]), 1)
        self.assertEqual(len(self.data["refund"]), 1)

    def test_create_refund_unique_ids(self):
        """Test that each refund gets a unique ID."""
        ids = set()
        for i in range(5):
            result = CreateRefund.invoke(
                self.data,
                payment_id="payment1",
                amount=10.0,
                currency="USD",
                reason="customer_remorse",
            )
            result_dict = json.loads(result)
            ids.add(result_dict["id"])
        
        # All IDs should be unique
        self.assertEqual(len(ids), 5)
        # All should start with "refund_"
        for refund_id in ids:
            self.assertTrue(refund_id.startswith("refund_"))

    def test_create_refund_mutates_data_in_place(self):
        """Test that the tool mutates data in place (write tool behavior)."""
        initial_refund_count = len(self.data.get("Refund", []))
        
        CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        
        # Data should be mutated
        self.assertEqual(len(self.data["Refund"]), initial_refund_count + 1)
        
        # Create another one
        CreateRefund.invoke(
            self.data,
            payment_id="payment2",
            amount=50.0,
            currency="USD",
            reason="defective",
        )
        
        # Should have 2 more
        self.assertEqual(len(self.data["Refund"]), initial_refund_count + 2)

    def test_create_refund_amount_as_float(self):
        """Test that amount is properly converted to float."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100,  # Integer
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        
        self.assertIsInstance(result_dict["amount"], float)
        self.assertEqual(result_dict["amount"], 100.0)

    def test_create_refund_default_status(self):
        """Test that status defaults to 'pending' if not provided."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["status"], "pending")

    def test_create_refund_none_status_defaults(self):
        """Test that None status defaults to 'pending'."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
            status=None,
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["status"], "pending")

    def test_create_refund_empty_lines_defaults(self):
        """Test that None lines defaults to empty list."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
            lines=None,
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["lines"], [])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CreateRefund.get_info()
        
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "create_refund")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("payment_id", info["function"]["parameters"]["properties"])
        self.assertIn("amount", info["function"]["parameters"]["properties"])
        self.assertIn("currency", info["function"]["parameters"]["properties"])
        self.assertIn("reason", info["function"]["parameters"]["properties"])
        self.assertIn("notes", info["function"]["parameters"]["properties"])
        self.assertIn("status", info["function"]["parameters"]["properties"])
        self.assertIn("lines", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("payment_id", required)
        self.assertIn("amount", required)
        self.assertIn("currency", required)
        self.assertIn("reason", required)
        self.assertNotIn("notes", required)
        self.assertNotIn("status", required)
        self.assertNotIn("lines", required)


if __name__ == "__main__":
    unittest.main()

