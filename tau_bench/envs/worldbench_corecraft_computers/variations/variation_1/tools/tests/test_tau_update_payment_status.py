import json
import unittest
from typing import Dict, Any

from ..tau_update_payment_status import UpdatePaymentStatus


class TestUpdatePaymentStatus(unittest.TestCase):
    def setUp(self):
        """Set up test data with payments."""
        self.data: Dict[str, Any] = {
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 100.0,
                    "method": "card",
                    "status": "pending",
                    "transactionId": "TXN-001",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order1",
                    "amount": 150.0,
                    "method": "paypal",
                    "status": "authorized",
                    "transactionId": "TXN-002",
                },
                "payment3": {
                    "id": "payment3",
                    "orderId": "order2",
                    "amount": 200.0,
                    "method": "card",
                    "status": "captured",
                    "transactionId": "TXN-003",
                },
            }
        }

    def test_update_payment_status_basic(self):
        """Test updating payment status."""
        result = UpdatePaymentStatus.invoke(
            self.data,
            payment_id="payment1",
            status="captured",
        )
        result_dict = json.loads(result)

        # Should return updated=True
        self.assertTrue(result_dict["updated"])

        # Should mutate data in place
        self.assertEqual(self.data["payment"]["payment1"]["status"], "captured")

    def test_update_payment_status_different_statuses(self):
        """Test updating to different status values."""
        statuses = ["pending", "authorized", "captured", "failed", "refunded", "disputed", "voided"]

        for status in statuses:
            # Reset payment1 status
            self.data["payment"]["payment1"]["status"] = "pending"

            result = UpdatePaymentStatus.invoke(
                self.data,
                payment_id="payment1",
                status=status,
            )
            result_dict = json.loads(result)

            self.assertTrue(result_dict["updated"])
            self.assertEqual(self.data["payment"]["payment1"]["status"], status)

    def test_update_payment_status_with_failure_reason(self):
        """Test updating payment status with failure_reason."""
        result = UpdatePaymentStatus.invoke(
            self.data,
            payment_id="payment1",
            status="failed",
            failure_reason="Insufficient funds",
        )
        result_dict = json.loads(result)

        self.assertTrue(result_dict["updated"])
        self.assertEqual(self.data["payment"]["payment1"]["status"], "failed")
        self.assertEqual(self.data["payment"]["payment1"]["failure_reason"], "Insufficient funds")

    def test_update_payment_status_nonexistent_payment(self):
        """Test updating non-existent payment."""
        result = UpdatePaymentStatus.invoke(
            self.data,
            payment_id="nonexistent",
            status="captured",
        )
        result_dict = json.loads(result)

        # Should return updated=False
        self.assertFalse(result_dict["updated"])

        # Data should not be changed
        self.assertEqual(len(self.data["payment"]), 3)

    def test_update_payment_status_multiple_updates(self):
        """Test updating the same payment multiple times."""
        # First update
        result1 = UpdatePaymentStatus.invoke(
            self.data,
            payment_id="payment1",
            status="authorized",
        )
        result_dict1 = json.loads(result1)

        self.assertTrue(result_dict1["updated"])
        self.assertEqual(self.data["payment"]["payment1"]["status"], "authorized")

        # Second update
        result2 = UpdatePaymentStatus.invoke(
            self.data,
            payment_id="payment1",
            status="captured",
        )
        result_dict2 = json.loads(result2)

        self.assertTrue(result_dict2["updated"])
        self.assertEqual(self.data["payment"]["payment1"]["status"], "captured")

    def test_update_payment_status_other_payments_unchanged(self):
        """Test that other payments are not affected."""
        initial_status_payment2 = self.data["payment"]["payment2"]["status"]

        result = UpdatePaymentStatus.invoke(
            self.data,
            payment_id="payment1",
            status="captured",
        )
        result_dict = json.loads(result)

        self.assertTrue(result_dict["updated"])

        # payment2 should be unchanged
        self.assertEqual(self.data["payment"]["payment2"]["status"], initial_status_payment2)

        # payment3 should be unchanged
        self.assertEqual(self.data["payment"]["payment3"]["status"], "captured")

    def test_update_payment_status_mutates_data_in_place(self):
        """Test that the tool mutates data in place (write tool behavior)."""
        # Get initial reference to payment
        payment1_initial = self.data["payment"]["payment1"]
        self.assertIsNotNone(payment1_initial)

        result = UpdatePaymentStatus.invoke(
            self.data,
            payment_id="payment1",
            status="captured",
        )
        result_dict = json.loads(result)

        self.assertTrue(result_dict["updated"])

        # The same object should be mutated
        self.assertIs(payment1_initial, self.data["payment"]["payment1"])
        self.assertEqual(payment1_initial["status"], "captured")

    def test_update_payment_status_all_fields_preserved(self):
        """Test that other fields in the payment are preserved."""
        payment1_initial = self.data["payment"]["payment1"]
        initial_order_id = payment1_initial["orderId"]
        initial_amount = payment1_initial["amount"]
        initial_method = payment1_initial["method"]

        result = UpdatePaymentStatus.invoke(
            self.data,
            payment_id="payment1",
            status="captured",
        )
        result_dict = json.loads(result)

        self.assertTrue(result_dict["updated"])

        # Other fields should be preserved
        self.assertEqual(self.data["payment"]["payment1"]["orderId"], initial_order_id)
        self.assertEqual(self.data["payment"]["payment1"]["amount"], initial_amount)
        self.assertEqual(self.data["payment"]["payment1"]["method"], initial_method)
        self.assertEqual(self.data["payment"]["payment1"]["status"], "captured")

    def test_update_payment_status_empty_payments(self):
        """Test updating when payments dict is empty."""
        empty_data = {"payment": {}}

        result = UpdatePaymentStatus.invoke(
            empty_data,
            payment_id="payment1",
            status="captured",
        )
        result_dict = json.loads(result)

        # Should return updated=False
        self.assertFalse(result_dict["updated"])

    def test_update_payment_status_missing_payments_key(self):
        """Test updating when payment key doesn't exist."""
        data_no_payments = {}

        result = UpdatePaymentStatus.invoke(
            data_no_payments,
            payment_id="payment1",
            status="captured",
        )
        result_dict = json.loads(result)

        # Should return updated=False
        self.assertFalse(result_dict["updated"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = UpdatePaymentStatus.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "updatePaymentStatus")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("payment_id", info["function"]["parameters"]["properties"])
        self.assertIn("status", info["function"]["parameters"]["properties"])
        self.assertIn("failure_reason", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("payment_id", required)
        self.assertIn("status", required)


if __name__ == "__main__":
    unittest.main()
