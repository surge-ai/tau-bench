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

from tau_create_escalation import CreateEscalation


class TestCreateEscalation(unittest.TestCase):
    def setUp(self):
        """Set up test data with support tickets."""
        self.data: Dict[str, Any] = {
            "SupportTicket": {
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
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        # Check that escalation was created with correct fields
        self.assertIn("id", result_dict)
        self.assertTrue(result_dict["id"].startswith("esc_"))
        self.assertEqual(result_dict["type"], "escalation")
        self.assertEqual(result_dict["ticketId"], "ticket1")
        self.assertEqual(result_dict["escalationType"], "technical")
        self.assertEqual(result_dict["destination"], "engineering")
        self.assertIsNone(result_dict["notes"])
        self.assertIsNone(result_dict["resolvedAt"])
        self.assertIn("createdAt", result_dict)
        
        # Check that escalation was added to data
        self.assertIn("Escalation", self.data)
        self.assertEqual(len(self.data["Escalation"]), 1)
        self.assertEqual(self.data["Escalation"][0]["ticketId"], "ticket1")

    def test_create_escalation_with_notes(self):
        """Test creating an escalation with notes."""
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="policy_exception",
            destination="operations",
            notes="Customer needs special handling",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["notes"], "Customer needs special handling")
        self.assertEqual(result_dict["escalationType"], "policy_exception")
        self.assertEqual(result_dict["destination"], "operations")

    def test_create_escalation_multiple(self):
        """Test creating multiple escalations for different tickets."""
        # Create first escalation
        result1 = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        result1_dict = json.loads(result1)
        
        # Create second escalation
        result2 = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket2",
            escalation_type="product_specialist",
            destination="product_management",
        )
        result2_dict = json.loads(result2)
        
        # Check both were created
        self.assertEqual(len(self.data["Escalation"]), 2)
        self.assertNotEqual(result1_dict["id"], result2_dict["id"])
        self.assertEqual(result1_dict["ticketId"], "ticket1")
        self.assertEqual(result2_dict["ticketId"], "ticket2")

    def test_create_escalation_nonexistent_ticket(self):
        """Test that creating escalation for non-existent ticket raises error."""
        with self.assertRaises(ValueError) as context:
            CreateEscalation.invoke(
                self.data,
                ticket_id="nonexistent",
                escalation_type="technical",
                destination="engineering",
            )
        
        self.assertIn("not found", str(context.exception))

    def test_create_escalation_ticket_in_list_format(self):
        """Test that tickets can be in list format."""
        data_list = {
            "SupportTicket": [
                {
                    "id": "ticket_list",
                    "customerId": "customer1",
                    "status": "open",
                }
            ]
        }
        
        result = CreateEscalation.invoke(
            data_list,
            ticket_id="ticket_list",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["ticketId"], "ticket_list")
        self.assertIn("Escalation", data_list)
        self.assertEqual(len(data_list["Escalation"]), 1)

    def test_create_escalation_different_ticket_key_names(self):
        """Test that tickets can be found under different key names."""
        # Test with lowercase key
        data_lower = {
            "support_ticket": {
                "ticket_lower": {
                    "id": "ticket_lower",
                    "status": "open",
                }
            }
        }
        
        result = CreateEscalation.invoke(
            data_lower,
            ticket_id="ticket_lower",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        self.assertEqual(result_dict["ticketId"], "ticket_lower")
        
        # Test with supportTickets (camelCase)
        data_camel = {
            "supportTickets": {
                "ticket_camel": {
                    "id": "ticket_camel",
                    "status": "open",
                }
            }
        }
        
        result = CreateEscalation.invoke(
            data_camel,
            ticket_id="ticket_camel",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        self.assertEqual(result_dict["ticketId"], "ticket_camel")

    def test_create_escalation_uses_custom_timestamp(self):
        """Test that escalation uses custom timestamp from data if available."""
        self.data["__now"] = "2025-09-15T12:30:00Z"
        
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["createdAt"], "2025-09-15T12:30:00Z")

    def test_create_escalation_uses_alternative_timestamp_keys(self):
        """Test that escalation uses alternative timestamp keys."""
        # Test with "now" key
        self.data["now"] = "2025-10-01T08:00:00Z"
        
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["createdAt"], "2025-10-01T08:00:00Z")
        
        # Test with "current_time" key
        self.data.pop("now")
        self.data["current_time"] = "2025-11-01T10:00:00Z"
        
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket2",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["createdAt"], "2025-11-01T10:00:00Z")

    def test_create_escalation_defaults_to_constant_timestamp(self):
        """Test that escalation defaults to constant timestamp if none provided."""
        # Remove any timestamp keys
        self.data.pop("__now", None)
        self.data.pop("now", None)
        self.data.pop("current_time", None)
        self.data.pop("currentTime", None)
        
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        # Should default to constant
        self.assertEqual(result_dict["createdAt"], "1970-01-01T00:00:00Z")

    def test_create_escalation_creates_lowercase_alias(self):
        """Test that escalation is also added to lowercase alias if present."""
        self.data["escalations"] = []
        
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        # Should be in both Escalation and escalations
        self.assertEqual(len(self.data["Escalation"]), 1)
        self.assertEqual(len(self.data["escalations"]), 1)
        self.assertEqual(self.data["Escalation"][0]["id"], result_dict["id"])
        self.assertEqual(self.data["escalations"][0]["id"], result_dict["id"])

    def test_create_escalation_creates_singular_lowercase_alias(self):
        """Test that escalation is added to singular lowercase alias if present."""
        self.data["escalation"] = []
        
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        # Should be in both Escalation and escalation
        self.assertEqual(len(self.data["Escalation"]), 1)
        self.assertEqual(len(self.data["escalation"]), 1)

    def test_create_escalation_handles_existing_escalations_list(self):
        """Test that escalation is added to existing escalations list."""
        self.data["Escalation"] = [
            {
                "id": "existing_esc",
                "ticketId": "ticket2",
                "escalationType": "old",
                "destination": "old_dest",
            }
        ]
        
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        # Should have 2 escalations now
        self.assertEqual(len(self.data["Escalation"]), 2)
        self.assertEqual(self.data["Escalation"][0]["id"], "existing_esc")
        self.assertEqual(self.data["Escalation"][1]["id"], result_dict["id"])

    def test_create_escalation_handles_existing_escalations_dict(self):
        """Test that escalation is added when Escalation is a dict."""
        self.data["Escalation"] = {
            "existing_esc": {
                "id": "existing_esc",
                "ticketId": "ticket2",
                "escalationType": "old",
                "destination": "old_dest",
            }
        }
        
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        result_dict = json.loads(result)
        
        # Should be converted to list and have 2 escalations
        self.assertIsInstance(self.data["Escalation"], list)
        self.assertEqual(len(self.data["Escalation"]), 2)

    def test_create_escalation_unique_ids(self):
        """Test that each escalation gets a unique ID."""
        ids = set()
        for i in range(5):
            result = CreateEscalation.invoke(
                self.data,
                ticket_id="ticket1",
                escalation_type="technical",
                destination="engineering",
            )
            result_dict = json.loads(result)
            ids.add(result_dict["id"])
        
        # All IDs should be unique
        self.assertEqual(len(ids), 5)
        # All should start with "esc_"
        for esc_id in ids:
            self.assertTrue(esc_id.startswith("esc_"))

    def test_create_escalation_mutates_data_in_place(self):
        """Test that the tool mutates data in place (write tool behavior)."""
        initial_escalation_count = len(self.data.get("Escalation", []))
        
        CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )
        
        # Data should be mutated
        self.assertEqual(len(self.data["Escalation"]), initial_escalation_count + 1)
        
        # Create another one
        CreateEscalation.invoke(
            self.data,
            ticket_id="ticket2",
            escalation_type="product_specialist",
            destination="product_management",
        )
        
        # Should have 2 more
        self.assertEqual(len(self.data["Escalation"]), initial_escalation_count + 2)

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
        self.assertIn("notes", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("ticket_id", required)
        self.assertIn("escalation_type", required)
        self.assertIn("destination", required)
        self.assertNotIn("notes", required)  # Notes should be optional

    def test_create_escalation_empty_notes(self):
        """Test that empty string notes are handled correctly."""
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
            notes="",
        )
        result_dict = json.loads(result)
        
        # Empty string should be stored as empty string, not None
        self.assertEqual(result_dict["notes"], "")

    def test_create_escalation_all_fields(self):
        """Test creating escalation with all fields populated."""
        result = CreateEscalation.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="policy_exception",
            destination="operations",
            notes="Full escalation with all details",
        )
        result_dict = json.loads(result)
        
        # Verify all fields
        self.assertIn("id", result_dict)
        self.assertEqual(result_dict["type"], "escalation")
        self.assertEqual(result_dict["ticketId"], "ticket1")
        self.assertEqual(result_dict["escalationType"], "policy_exception")
        self.assertEqual(result_dict["destination"], "operations")
        self.assertEqual(result_dict["notes"], "Full escalation with all details")
        self.assertIsNone(result_dict["resolvedAt"])
        self.assertIn("createdAt", result_dict)


if __name__ == "__main__":
    unittest.main()

