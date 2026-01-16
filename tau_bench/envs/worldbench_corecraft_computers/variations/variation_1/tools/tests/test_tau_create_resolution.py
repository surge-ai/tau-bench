import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_create_resolution import CreateResolution


class TestCreateResolution(unittest.TestCase):
    def setUp(self):
        """Set up test data with support tickets, employees, and refunds."""
        self.data: Dict[str, Any] = {
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "open",
                    "priority": "high",
                    "subject": "Test ticket 1",
                    "createdAt": "2025-01-01T00:00:00Z",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer2",
                    "status": "new",
                    "priority": "medium",
                    "subject": "Test ticket 2",
                    "createdAt": "2025-01-02T00:00:00Z",
                },
            },
            "employee": {
                "emp1": {
                    "id": "emp1",
                    "name": "John Doe",
                    "role": "support_agent",
                },
                "emp2": {
                    "id": "emp2",
                    "name": "Jane Smith",
                    "role": "manager",
                },
            },
            "refund": {
                "refund1": {
                    "id": "refund1",
                    "amount": 100.0,
                    "status": "approved",
                },
            },
        }

    def test_create_resolution_basic(self):
        """Test creating a basic resolution."""
        result_dict = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
        )

        # Check that resolution was created with correct fields
        self.assertIn("id", result_dict)
        self.assertTrue(result_dict["id"].startswith("res_"))
        self.assertEqual(result_dict["type"], "resolution")
        self.assertEqual(result_dict["ticketId"], "ticket1")
        self.assertEqual(result_dict["outcome"], "troubleshooting_steps")

    def test_create_resolution_with_resolved_by(self):
        """Test creating resolution with resolved_by_id."""
        result_dict = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
            resolved_by_id="emp1",
        )

        self.assertEqual(result_dict["resolvedById"], "emp1")

    def test_create_resolution_with_linked_refund(self):
        """Test creating resolution with linked refund."""
        result_dict = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="refund_issued",
            linked_refund_id="refund1",
        )

        self.assertEqual(result_dict["linkedRefundId"], "refund1")

    def test_create_resolution_invalid_ticket(self):
        """Test creating resolution for non-existent ticket."""
        result = CreateResolution.invoke(
                self.data,
                ticket_id="nonexistent",
                outcome="troubleshooting_steps",
)

        self.assertIn("error", result)

    def test_create_resolution_invalid_refund(self):
        """Test creating resolution with non-existent refund."""
        result = CreateResolution.invoke(
                self.data,
                ticket_id="ticket1",
                outcome="refund_issued",
                linked_refund_id="nonexistent",
)

        self.assertIn("error", result)

    def test_create_resolution_invalid_employee(self):
        """Test creating resolution with non-existent employee."""
        result = CreateResolution.invoke(
                self.data,
                ticket_id="ticket1",
                outcome="troubleshooting_steps",
                resolved_by_id="nonexistent",
)

        self.assertIn("error", result)

    def test_create_resolution_mutates_data_in_place(self):
        """Test that the tool adds resolution to data dict."""
        result_dict = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
        )

        # Check that resolution was added to data
        self.assertIn("resolution", self.data)
        self.assertIn(result_dict["id"], self.data["resolution"])

    def test_create_resolution_unique_ids(self):
        """Test that resolutions get unique IDs based on parameters."""
        # Create first resolution
        result1_dict = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
        )

        # Create second resolution with different parameters
        result2_dict = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="recommendation_provided",
        )

        # IDs should be different
        self.assertNotEqual(result1_dict["id"], result2_dict["id"])

    def test_create_resolution_uses_custom_timestamp(self):
        """Test that resolution uses custom timestamp from data if provided."""
        self.data["__now"] = "2025-06-15T12:00:00Z"

        result_dict = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
        )

        self.assertEqual(result_dict["createdAt"], "2025-06-15T12:00:00Z")

    def test_create_resolution_optional_refund_not_required(self):
        """Test that linked_refund_id is optional."""
        result_dict = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
        )

        self.assertIsNone(result_dict["linkedRefundId"])

    def test_create_resolution_optional_employee_not_required(self):
        """Test that resolved_by_id is optional."""
        result_dict = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
        )

        self.assertIsNone(result_dict["resolvedById"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CreateResolution.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "create_resolution")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("ticket_id", info["function"]["parameters"]["properties"])
        self.assertIn("outcome", info["function"]["parameters"]["properties"])
        self.assertIn("linked_refund_id", info["function"]["parameters"]["properties"])
        self.assertIn("resolved_by_id", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("ticket_id", required)
        self.assertIn("outcome", required)


if __name__ == "__main__":
    unittest.main()
