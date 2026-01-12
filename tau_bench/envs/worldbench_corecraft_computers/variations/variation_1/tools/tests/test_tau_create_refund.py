import json
import unittest
from typing import Dict, Any

from ..tau_create_refund import CreateRefund


class TestCreateRefund(unittest.TestCase):
    def setUp(self):
        """Set up test data with payments."""
        self.data: Dict[str, Any] = {
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 100.0,
                    "currency": "USD",
                    "method": "card",
                    "status": "captured",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order2",
                    "amount": 250.5,
                    "currency": "USD",
                    "method": "card",
                    "status": "captured",
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

    def test_create_refund_with_status(self):
        """Test creating refund with specific status."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="defective",
            status="approved",
        )
        result_dict = json.loads(result)

        self.assertEqual(result_dict["status"], "approved")

    def test_create_refund_default_status(self):
        """Test that status defaults to pending."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="incompatible",
        )
        result_dict = json.loads(result)

        self.assertEqual(result_dict["status"], "pending")

    def test_create_refund_with_lines(self):
        """Test creating refund with line items."""
        lines = [
            {"productId": "prod1", "qty": 1, "amount": 50.0},
            {"productId": "prod2", "qty": 2, "amount": 50.0},
        ]
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
            lines=lines,
        )
        result_dict = json.loads(result)

        self.assertIsInstance(result_dict["lines"], list)
        self.assertEqual(len(result_dict["lines"]), 2)

    def test_create_refund_invalid_payment(self):
        """Test creating refund for non-existent payment."""
        with self.assertRaises(ValueError):
            CreateRefund.invoke(
                self.data,
                payment_id="nonexistent",
                amount=100.0,
                currency="USD",
                reason="customer_remorse",
            )

    def test_create_refund_mutates_data_in_place(self):
        """Test that the tool adds refund to data dict."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)

        # Check that refund was added to data
        self.assertIn("refund", self.data)
        self.assertIn(result_dict["id"], self.data["refund"])

    def test_create_refund_unique_ids(self):
        """Test that refunds get unique IDs based on parameters."""
        # Create first refund
        result1 = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result1_dict = json.loads(result1)

        # Create second refund with different parameters
        result2 = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=50.0,
            currency="USD",
            reason="defective",
        )
        result2_dict = json.loads(result2)

        # IDs should be different
        self.assertNotEqual(result1_dict["id"], result2_dict["id"])

    def test_create_refund_uses_custom_timestamp(self):
        """Test that refund uses custom timestamp from data if provided."""
        self.data["__now"] = "2025-06-15T12:00:00Z"

        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)

        self.assertEqual(result_dict["createdAt"], "2025-06-15T12:00:00Z")

    def test_create_refund_defaults_to_constant_timestamp(self):
        """Test that refund uses constant timestamp when not provided."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)

        self.assertEqual(result_dict["createdAt"], "1970-01-01T00:00:00Z")

    def test_create_refund_processed_at_is_none(self):
        """Test that processedAt is None on creation."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)

        self.assertIsNone(result_dict["processedAt"])

    def test_create_refund_amount_as_float(self):
        """Test that amount is stored as float."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100,  # Integer input
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)

        self.assertIsInstance(result_dict["amount"], float)
        self.assertEqual(result_dict["amount"], 100.0)

    def test_create_refund_empty_lines_defaults(self):
        """Test that lines defaults to empty list."""
        result = CreateRefund.invoke(
            self.data,
            payment_id="payment1",
            amount=100.0,
            currency="USD",
            reason="customer_remorse",
        )
        result_dict = json.loads(result)

        self.assertIsInstance(result_dict["lines"], list)
        self.assertEqual(len(result_dict["lines"]), 0)

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
        self.assertIn("status", info["function"]["parameters"]["properties"])
        self.assertIn("lines", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("payment_id", required)
        self.assertIn("amount", required)
        self.assertIn("currency", required)
        self.assertIn("reason", required)


if __name__ == "__main__":
    unittest.main()
