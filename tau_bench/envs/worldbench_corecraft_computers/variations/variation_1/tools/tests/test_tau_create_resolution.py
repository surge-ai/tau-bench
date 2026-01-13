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

from tau_create_resolution import CreateResolution


class TestCreateResolution(unittest.TestCase):
    def setUp(self):
        """Set up test data with tickets, refunds, and employees."""
        self.data: Dict[str, Any] = {
            "SupportTicket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "open",
                    "priority": "high",
                    "subject": "Test ticket 1",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer2",
                    "status": "new",
                    "priority": "medium",
                    "subject": "Test ticket 2",
                },
            },
            "Refund": {
                "refund1": {
                    "id": "refund1",
                    "paymentId": "payment1",
                    "amount": 100.0,
                    "status": "processed",
                },
                "refund2": {
                    "id": "refund2",
                    "paymentId": "payment2",
                    "amount": 50.0,
                    "status": "approved",
                },
            },
            "Employee": {
                "employee1": {
                    "id": "employee1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "department": "support",
                },
                "employee2": {
                    "id": "employee2",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "department": "engineering",
                },
            },
        }

    def test_create_resolution_basic(self):
        """Test creating a basic resolution."""
        result = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="refund_approved",
        )
        result_dict = json.loads(result)
        
        # Check that resolution was created with correct fields
        self.assertIn("id", result_dict)
        self.assertTrue(result_dict["id"].startswith("res_"))
        self.assertEqual(result_dict["type"], "resolution")
        self.assertEqual(result_dict["ticketId"], "ticket1")
        self.assertEqual(result_dict["outcome"], "refund_approved")
        self.assertIsNone(result_dict["linkedRefundId"])
        self.assertIsNone(result_dict["resolvedById"])
        self.assertIsNone(result_dict["notes"])
        self.assertIn("createdAt", result_dict)
        
        # Check that resolution was added to data
        self.assertIn("Resolution", self.data)
        self.assertEqual(len(self.data["Resolution"]), 1)
        self.assertEqual(self.data["Resolution"][0]["ticketId"], "ticket1")

    def test_create_resolution_with_linked_refund(self):
        """Test creating a resolution with linked refund."""
        result = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="refund_issued",
            linked_refund_id="refund1",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["linkedRefundId"], "refund1")
        self.assertEqual(result_dict["outcome"], "refund_issued")

    def test_create_resolution_with_resolved_by(self):
        """Test creating a resolution with resolved_by employee."""
        result = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
            resolved_by_id="employee1",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["resolvedById"], "employee1")

    def test_create_resolution_with_notes(self):
        """Test creating a resolution with notes."""
        result = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="replacement_provided",
            notes="Customer received replacement product",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["notes"], "Customer received replacement product")

    def test_create_resolution_all_fields(self):
        """Test creating a resolution with all fields populated."""
        result = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="refund_issued",
            linked_refund_id="refund1",
            resolved_by_id="employee1",
            notes="Full resolution with all details",
        )
        result_dict = json.loads(result)
        
        # Verify all fields
        self.assertIn("id", result_dict)
        self.assertEqual(result_dict["type"], "resolution")
        self.assertEqual(result_dict["ticketId"], "ticket1")
        self.assertEqual(result_dict["outcome"], "refund_issued")
        self.assertEqual(result_dict["linkedRefundId"], "refund1")
        self.assertEqual(result_dict["resolvedById"], "employee1")
        self.assertEqual(result_dict["notes"], "Full resolution with all details")
        self.assertIn("createdAt", result_dict)

    def test_create_resolution_nonexistent_ticket(self):
        """Test that creating resolution for non-existent ticket raises error."""
        with self.assertRaises(ValueError) as context:
            CreateResolution.invoke(
                self.data,
                ticket_id="nonexistent",
                outcome="refund_approved",
            )
        
        self.assertIn("not found", str(context.exception))

    def test_create_resolution_nonexistent_refund(self):
        """Test that creating resolution with non-existent refund raises error."""
        with self.assertRaises(ValueError) as context:
            CreateResolution.invoke(
                self.data,
                ticket_id="ticket1",
                outcome="refund_issued",
                linked_refund_id="nonexistent_refund",
            )
        
        self.assertIn("not found", str(context.exception))

    def test_create_resolution_nonexistent_employee(self):
        """Test that creating resolution with non-existent employee raises error."""
        with self.assertRaises(ValueError) as context:
            CreateResolution.invoke(
                self.data,
                ticket_id="ticket1",
                outcome="troubleshooting_steps",
                resolved_by_id="nonexistent_employee",
            )
        
        self.assertIn("not found", str(context.exception))

    def test_create_resolution_different_ticket_key_names(self):
        """Test that tickets can be found under different key names."""
        # Test with lowercase key
        data_lower = {
            "support_tickets": {
                "ticket_lower": {
                    "id": "ticket_lower",
                    "status": "open",
                }
            }
        }
        
        result = CreateResolution.invoke(
            data_lower,
            ticket_id="ticket_lower",
            outcome="refund_approved",
        )
        result_dict = json.loads(result)
        self.assertEqual(result_dict["ticketId"], "ticket_lower")
        
        # Test with "tickets" key
        data_tickets = {
            "tickets": {
                "ticket_tickets": {
                    "id": "ticket_tickets",
                    "status": "open",
                }
            }
        }
        
        result = CreateResolution.invoke(
            data_tickets,
            ticket_id="ticket_tickets",
            outcome="refund_approved",
        )
        result_dict = json.loads(result)
        self.assertEqual(result_dict["ticketId"], "ticket_tickets")

    def test_create_resolution_different_refund_key_names(self):
        """Test that refunds can be found under different key names."""
        data_with_refunds = {
            "SupportTicket": {
                "ticket1": {"id": "ticket1", "status": "open"}
            },
            "refunds": {
                "refund_lower": {
                    "id": "refund_lower",
                    "amount": 100.0,
                }
            }
        }
        
        result = CreateResolution.invoke(
            data_with_refunds,
            ticket_id="ticket1",
            outcome="refund_issued",
            linked_refund_id="refund_lower",
        )
        result_dict = json.loads(result)
        self.assertEqual(result_dict["linkedRefundId"], "refund_lower")

    def test_create_resolution_different_employee_key_names(self):
        """Test that employees can be found under different key names."""
        data_with_employees = {
            "SupportTicket": {
                "ticket1": {"id": "ticket1", "status": "open"}
            },
            "employees": {
                "emp_lower": {
                    "id": "emp_lower",
                    "name": "Test Employee",
                }
            }
        }
        
        result = CreateResolution.invoke(
            data_with_employees,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
            resolved_by_id="emp_lower",
        )
        result_dict = json.loads(result)
        self.assertEqual(result_dict["resolvedById"], "emp_lower")

    def test_create_resolution_uses_custom_timestamp(self):
        """Test that resolution uses custom timestamp from data if available."""
        self.data["__now"] = "2025-09-15T12:30:00Z"
        
        result = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="refund_approved",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["createdAt"], "2025-09-15T12:30:00Z")

    def test_create_resolution_creates_lowercase_alias(self):
        """Test that resolution is also added to lowercase alias if present."""
        self.data["resolutions"] = []
        
        result = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="refund_approved",
        )
        result_dict = json.loads(result)
        
        # Should be in both Resolution and resolutions
        self.assertEqual(len(self.data["Resolution"]), 1)
        self.assertEqual(len(self.data["resolutions"]), 1)
        self.assertEqual(self.data["Resolution"][0]["id"], result_dict["id"])
        self.assertEqual(self.data["resolutions"][0]["id"], result_dict["id"])

    def test_create_resolution_unique_ids(self):
        """Test that each resolution gets a unique ID."""
        ids = set()
        for i in range(5):
            result = CreateResolution.invoke(
                self.data,
                ticket_id="ticket1",
                outcome="refund_approved",
            )
            result_dict = json.loads(result)
            ids.add(result_dict["id"])
        
        # All IDs should be unique
        self.assertEqual(len(ids), 5)
        # All should start with "res_"
        for res_id in ids:
            self.assertTrue(res_id.startswith("res_"))

    def test_create_resolution_mutates_data_in_place(self):
        """Test that the tool mutates data in place (write tool behavior)."""
        initial_resolution_count = len(self.data.get("Resolution", []))
        
        CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="refund_approved",
        )
        
        # Data should be mutated
        self.assertEqual(len(self.data["Resolution"]), initial_resolution_count + 1)
        
        # Create another one
        CreateResolution.invoke(
            self.data,
            ticket_id="ticket2",
            outcome="replacement_provided",
        )
        
        # Should have 2 more
        self.assertEqual(len(self.data["Resolution"]), initial_resolution_count + 2)

    def test_create_resolution_optional_refund_not_required(self):
        """Test that linked_refund_id is optional and None is valid."""
        result = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="troubleshooting_steps",
            linked_refund_id=None,
        )
        result_dict = json.loads(result)
        
        self.assertIsNone(result_dict["linkedRefundId"])

    def test_create_resolution_optional_employee_not_required(self):
        """Test that resolved_by_id is optional and None is valid."""
        result = CreateResolution.invoke(
            self.data,
            ticket_id="ticket1",
            outcome="no_action",
            resolved_by_id=None,
        )
        result_dict = json.loads(result)
        
        self.assertIsNone(result_dict["resolvedById"])

    def test_create_resolution_ticket_in_list_format(self):
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
        
        result = CreateResolution.invoke(
            data_list,
            ticket_id="ticket_list",
            outcome="refund_approved",
        )
        result_dict = json.loads(result)
        
        self.assertEqual(result_dict["ticketId"], "ticket_list")
        self.assertIn("Resolution", data_list)
        self.assertEqual(len(data_list["Resolution"]), 1)

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
        self.assertIn("notes", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("ticket_id", required)
        self.assertIn("outcome", required)
        self.assertNotIn("linked_refund_id", required)
        self.assertNotIn("resolved_by_id", required)
        self.assertNotIn("notes", required)


if __name__ == "__main__":
    unittest.main()

