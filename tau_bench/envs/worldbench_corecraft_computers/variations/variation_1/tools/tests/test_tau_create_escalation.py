import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_create_escalation import CreateEscalation


class TestCreateEscalation(unittest.TestCase):
    def setUp(self):
        """Set up test data with support tickets."""
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
            }
        }

    def test_create_escalation_basic(self):
        """Test creating a basic escalation."""
        result_dict = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        # Check that escalation was created with correct fields
        self.assertIn("id", result_dict)
        self.assertTrue(result_dict["id"].startswith("esc_"))
        self.assertEqual(result_dict["type"], "escalation")
        self.assertEqual(result_dict["ticketId"], "ticket1")
        self.assertEqual(result_dict["escalationType"], "technical")
        self.assertEqual(result_dict["destination"], "engineering")

    def test_create_escalation_different_types(self):
        """Test creating escalations with different types."""
        types = ["technical", "policy_exception", "product_specialist"]

        for esc_type in types:
            result_dict = CreateEscalation.invoke(
                self.data,
                ticket_id="ticket1",
                escalation_type=esc_type,
                destination="test_destination",
            )

            self.assertEqual(result_dict["escalationType"], esc_type)

    def test_create_escalation_invalid_ticket(self):
        """Test creating escalation for non-existent ticket."""
        result = CreateEscalation.invoke(
                self.data,
                ticket_id="nonexistent",
                escalation_type="technical",
                destination="engineering",
)

        self.assertIn("error", result)

    def test_create_escalation_mutates_data_in_place(self):
        """Test that the tool adds escalation to data dict."""
        result_dict = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        # Check that escalation was added to data
        self.assertIn("escalation", self.data)
        self.assertIn(result_dict["id"], self.data["escalation"])

    def test_create_escalation_unique_ids(self):
        """Test that escalations get unique IDs based on parameters."""
        # Create first escalation
        result1_dict = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        # Create second escalation with different parameters
        result2_dict = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="policy_exception",
            destination="management",
        )

        # IDs should be different
        self.assertNotEqual(result1_dict["id"], result2_dict["id"])

    def test_create_escalation_uses_custom_timestamp(self):
        """Test that escalation uses custom timestamp from data if provided."""
        self.data["__now"] = "2025-06-15T12:00:00Z"

        result_dict = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertEqual(result_dict["createdAt"], "2025-06-15T12:00:00Z")

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = CreateEscalation.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "create_escalation")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("ticket_id", info["function"]["parameters"]["properties"])
        self.assertIn("escalation_type", info["function"]["parameters"]["properties"])
        self.assertIn("destination", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("ticket_id", required)
        self.assertIn("escalation_type", required)
        self.assertIn("destination", required)


if __name__ == "__main__":
    unittest.main()
