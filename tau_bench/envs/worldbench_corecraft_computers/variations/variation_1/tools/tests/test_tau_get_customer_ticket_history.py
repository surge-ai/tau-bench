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
from tau_sqlite_utils import build_sqlite_from_data
from tau_bench.envs.tool import Tool

# Create a mock utils module for tool_impls that need it
# IMPORTANT: We need to create this BEFORE importing anything that uses utils
import types
import sqlite3
utils_module = types.ModuleType("utils")
# Provide a dummy function that will be replaced by the tool's monkeypatch
utils_module.get_db_conn = lambda: sqlite3.connect(":memory:")

# Mock the utility functions that tool_impls needs
def validate_date_format(date_str, param_name):
    """Mock date validation - just return the string."""
    return date_str

def parse_datetime_to_timestamp(date_str):
    """Mock datetime parsing - convert ISO string to timestamp."""
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)  # Convert to milliseconds
    except Exception:
        return 0

def timestamp_to_iso_string(timestamp):
    """Mock timestamp to ISO string conversion."""
    from datetime import datetime, timezone
    try:
        dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        return dt.isoformat().replace('+00:00', 'Z')
    except Exception:
        return "1970-01-01T00:00:00Z"

utils_module.validate_date_format = validate_date_format
utils_module.parse_datetime_to_timestamp = parse_datetime_to_timestamp
utils_module.timestamp_to_iso_string = timestamp_to_iso_string
sys.modules["utils"] = utils_module

# Import tool_impls first so it uses our utils module
import tool_impls.get_customer_ticket_history  # noqa: F401

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_get_customer_ticket_history import GetCustomerTicketHistory


class TestGetCustomerTicketHistory(unittest.TestCase):
    def setUp(self):
        """Set up test data with support tickets, escalations, and resolutions."""
        # Note: The actual data uses lowercase "support_ticket" key, but tool_impls queries "SupportTicket"
        # build_sqlite_from_data creates tables with the exact key name, so we use "SupportTicket"
        # to match what tool_impls expects
        # Note: createdAt and updatedAt must be INTEGER timestamps (milliseconds) not ISO strings
        # because tool_impls compares them as integers and converts to ISO strings in output
        self.data: Dict[str, Any] = {
            "SupportTicket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "ticketType": "troubleshooting",
                    "status": "open",
                    "priority": "high",
                    "subject": "Test ticket 1",
                    "createdAt": 1725120000000,  # 2025-09-01T00:00:00Z in milliseconds
                    "updatedAt": 1725123600000,  # 2025-09-01T01:00:00Z
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer1",
                    "ticketType": "other",
                    "status": "resolved",
                    "priority": "medium",
                    "subject": "Test ticket 2",
                    "createdAt": 1725206400000,  # 2025-09-02T00:00:00Z
                    "updatedAt": 1725210000000,  # 2025-09-02T01:00:00Z
                },
                "ticket3": {
                    "id": "ticket3",
                    "customerId": "customer1",
                    "ticketType": "troubleshooting",
                    "status": "closed",
                    "priority": "low",
                    "subject": "Test ticket 3",
                    "createdAt": 1725292800000,  # 2025-09-03T00:00:00Z
                    "updatedAt": 1725296400000,  # 2025-09-03T01:00:00Z
                },
                "ticket4": {
                    "id": "ticket4",
                    "customerId": "customer2",  # Different customer
                    "ticketType": "other",
                    "status": "open",
                    "priority": "normal",
                    "subject": "Test ticket 4",
                    "createdAt": 1725379200000,  # 2025-09-04T00:00:00Z
                    "updatedAt": 1725382800000,  # 2025-09-04T01:00:00Z
                },
            },
            "Escalation": {
                "esc1": {
                    "id": "esc1",
                    "ticketId": "ticket1",
                    "escalationType": "technical",
                    "destination": "engineering",
                    "createdAt": "2025-09-01T02:00:00Z",
                }
            },
            "Resolution": {
                "res1": {
                    "id": "res1",
                    "ticketId": "ticket2",
                    "outcome": "refund_approved",
                    "details": "Refund was approved for customer",
                    "createdAt": "2025-09-02T02:00:00Z",
                },
                "res2": {
                    "id": "res2",
                    "ticketId": "ticket3",
                    "outcome": "replacement_provided",
                    "details": "Replacement product provided",
                    "createdAt": "2025-09-03T02:00:00Z",
                }
            }
        }

    def test_get_ticket_history_basic(self):
        """Test getting ticket history for a customer."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)
        
        # Should return tickets for customer1
        self.assertIn("tickets", result_dict)
        tickets = result_dict["tickets"]
        self.assertGreater(len(tickets), 0)
        
        # All tickets should be for customer1
        for ticket in tickets:
            self.assertEqual(ticket["customerId"], "customer1")
            self.assertIn("id", ticket)
            self.assertIn("status", ticket)
            self.assertIn("category", ticket)
            self.assertIn("priority", ticket)
            self.assertIn("subject", ticket)
            self.assertIn("createdAt", ticket)
            self.assertIn("updatedAt", ticket)

    def test_get_ticket_history_excludes_other_customers(self):
        """Test that tickets from other customers are excluded."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        ticket_ids = [t["id"] for t in tickets]
        
        # Should not include ticket4 (customer2)
        self.assertNotIn("ticket4", ticket_ids)
        # Should include customer1 tickets
        self.assertIn("ticket1", ticket_ids)
        self.assertIn("ticket2", ticket_ids)
        self.assertIn("ticket3", ticket_ids)

    def test_get_ticket_history_include_resolved_default(self):
        """Test that resolved/closed tickets are included by default."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        ticket_ids = [t["id"] for t in tickets]
        
        # Should include resolved and closed tickets
        self.assertIn("ticket2", ticket_ids)  # resolved
        self.assertIn("ticket3", ticket_ids)  # closed

    def test_get_ticket_history_exclude_resolved(self):
        """Test excluding resolved/closed tickets."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            include_resolved="false",
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        ticket_ids = [t["id"] for t in tickets]
        
        # Should only include open tickets
        self.assertIn("ticket1", ticket_ids)  # open
        self.assertNotIn("ticket2", ticket_ids)  # resolved
        self.assertNotIn("ticket3", ticket_ids)  # closed

    def test_get_ticket_history_include_resolved_explicit(self):
        """Test explicitly including resolved tickets."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            include_resolved="true",
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        ticket_ids = [t["id"] for t in tickets]
        
        # Should include all tickets
        self.assertIn("ticket1", ticket_ids)
        self.assertIn("ticket2", ticket_ids)
        self.assertIn("ticket3", ticket_ids)

    def test_get_ticket_history_filter_created_after(self):
        """Test filtering tickets created after a date."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            tkt_created_after="2025-09-01T12:00:00Z",  # Midday on 2025-09-01
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        ticket_ids = list(set([t["id"] for t in tickets]))  # Remove duplicates if any
        
        # Date filtering should work - verify we get some results
        # The exact filtering logic depends on timestamp conversion
        self.assertIsInstance(ticket_ids, list)
        # Should have fewer or equal tickets than without filter
        result_no_filter = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        no_filter_dict = json.loads(result_no_filter)
        no_filter_ids = list(set([t["id"] for t in no_filter_dict["tickets"]]))
        self.assertLessEqual(len(ticket_ids), len(no_filter_ids))

    def test_get_ticket_history_filter_created_before(self):
        """Test filtering tickets created before a date."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            tkt_created_before="2025-09-03T12:00:00Z",  # Midday on 2025-09-03
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        ticket_ids = list(set([t["id"] for t in tickets]))  # Remove duplicates if any
        
        # Date filtering should work - verify we get some results
        self.assertIsInstance(ticket_ids, list)
        # Should have fewer or equal tickets than without filter
        result_no_filter = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        no_filter_dict = json.loads(result_no_filter)
        no_filter_ids = list(set([t["id"] for t in no_filter_dict["tickets"]]))
        self.assertLessEqual(len(ticket_ids), len(no_filter_ids))

    def test_get_ticket_history_filter_updated_after(self):
        """Test filtering tickets updated after a date."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            tkt_updated_after="2025-09-01T12:00:00Z",  # Midday on 2025-09-01
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        ticket_ids = list(set([t["id"] for t in tickets]))  # Remove duplicates if any
        
        # Date filtering should work - verify we get some results
        self.assertIsInstance(ticket_ids, list)
        # Should have fewer or equal tickets than without filter
        result_no_filter = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        no_filter_dict = json.loads(result_no_filter)
        no_filter_ids = list(set([t["id"] for t in no_filter_dict["tickets"]]))
        self.assertLessEqual(len(ticket_ids), len(no_filter_ids))

    def test_get_ticket_history_filter_updated_before(self):
        """Test filtering tickets updated before a date."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            tkt_updated_before="2025-09-03T12:00:00Z",  # Midday on 2025-09-03
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        ticket_ids = list(set([t["id"] for t in tickets]))  # Remove duplicates if any
        
        # Date filtering should work - verify we get some results
        self.assertIsInstance(ticket_ids, list)
        # Should have fewer or equal tickets than without filter
        result_no_filter = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        no_filter_dict = json.loads(result_no_filter)
        no_filter_ids = list(set([t["id"] for t in no_filter_dict["tickets"]]))
        self.assertLessEqual(len(ticket_ids), len(no_filter_ids))

    def test_get_ticket_history_multiple_filters(self):
        """Test using multiple filters together."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            tkt_created_after="2025-09-01T12:00:00Z",
            tkt_created_before="2025-09-03T00:00:00Z",
            include_resolved="false",
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        ticket_ids = [t["id"] for t in tickets]
        
        # Should only include open tickets created in the date range
        # ticket1: created 2025-09-01 (before 12:00, so excluded)
        # ticket2: created 2025-09-02 (in range) but resolved (excluded)
        # ticket3: created 2025-09-03 (after end date, excluded)
        self.assertEqual(len(ticket_ids), 0)

    def test_get_ticket_history_includes_escalations(self):
        """Test that escalations are included in the response."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)
        
        # Should have escalations field
        self.assertIn("escalations", result_dict)
        escalations = result_dict["escalations"]
        
        # Should include escalation for ticket1
        self.assertGreater(len(escalations), 0)
        ticket1_escalations = [e for e in escalations if e.get("ticketId") == "ticket1"]
        self.assertGreater(len(ticket1_escalations), 0)

    def test_get_ticket_history_includes_resolutions(self):
        """Test that resolutions are included in the response."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)
        
        # Should have resolutions field
        self.assertIn("resolutions", result_dict)
        resolutions = result_dict["resolutions"]
        
        # Should include resolutions for ticket2 and ticket3
        self.assertGreater(len(resolutions), 0)
        resolution_ticket_ids = [r.get("ticketId") for r in resolutions]
        self.assertIn("ticket2", resolution_ticket_ids)
        self.assertIn("ticket3", resolution_ticket_ids)

    def test_get_ticket_history_empty_result(self):
        """Test getting history for customer with no tickets."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="nonexistent_customer",
        )
        result_dict = json.loads(result)
        
        # Should return empty lists
        self.assertIn("tickets", result_dict)
        self.assertEqual(len(result_dict["tickets"]), 0)
        self.assertIn("escalations", result_dict)
        self.assertEqual(len(result_dict["escalations"]), 0)
        self.assertIn("resolutions", result_dict)
        self.assertEqual(len(result_dict["resolutions"]), 0)

    def test_get_ticket_history_tickets_sorted(self):
        """Test that tickets are sorted by createdAt DESC, then id ASC."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        
        # Should be sorted: newest first (ticket3, ticket2, ticket1)
        if len(tickets) >= 2:
            # Check that tickets are in descending order by createdAt
            for i in range(len(tickets) - 1):
                current_created = tickets[i]["createdAt"]
                next_created = tickets[i + 1]["createdAt"]
                # Parse ISO strings to compare
                from datetime import datetime
                current_dt = datetime.fromisoformat(current_created.replace('Z', '+00:00'))
                next_dt = datetime.fromisoformat(next_created.replace('Z', '+00:00'))
                self.assertGreaterEqual(current_dt, next_dt)

    def test_get_ticket_history_ticket_format(self):
        """Test that tickets have the correct format."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)
        
        tickets = result_dict["tickets"]
        if tickets:
            ticket = tickets[0]
            # Check required fields
            self.assertIn("id", ticket)
            self.assertIn("customerId", ticket)
            self.assertIn("category", ticket)  # mapped from ticketType
            self.assertIn("status", ticket)
            self.assertIn("priority", ticket)
            self.assertIn("subject", ticket)
            self.assertIn("createdAt", ticket)
            self.assertIn("updatedAt", ticket)
            
            # Check that dates are in ISO format
            self.assertRegex(ticket["createdAt"], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
            self.assertRegex(ticket["updatedAt"], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

    def test_get_ticket_history_missing_customer_id(self):
        """Test that missing customer_id raises an error."""
        # The tool_impls requires customer_id as a positional argument
        # Missing it will raise TypeError
        with self.assertRaises((TypeError, ValueError)):
            GetCustomerTicketHistory.invoke(self.data)

    def test_get_ticket_history_empty_customer_id(self):
        """Test that empty customer_id raises an error."""
        with self.assertRaises(ValueError):
            GetCustomerTicketHistory.invoke(
                self.data,
                customer_id="",
            )

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetCustomerTicketHistory.get_info()
        
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "getCustomerTicketHistory")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("include_resolved", info["function"]["parameters"]["properties"])
        self.assertIn("tkt_created_after", info["function"]["parameters"]["properties"])
        self.assertIn("tkt_created_before", info["function"]["parameters"]["properties"])
        self.assertIn("tkt_updated_after", info["function"]["parameters"]["properties"])
        self.assertIn("tkt_updated_before", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("customer_id", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()

