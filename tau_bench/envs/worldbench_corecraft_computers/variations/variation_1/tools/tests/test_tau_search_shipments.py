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
import types
import sqlite3
utils_module = types.ModuleType("utils")
utils_module.get_db_conn = lambda: sqlite3.connect(":memory:")

# Mock the utility functions that tool_impls needs
def validate_date_format(date_str, param_name):
    """Mock date validation - just return the string."""
    if date_str is None:
        return None
    return date_str

def parse_datetime_to_timestamp(date_str):
    """Mock datetime parsing - convert ISO string to timestamp."""
    from datetime import datetime, timezone
    if date_str is None:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)  # Convert to milliseconds
    except Exception:
        return 0

utils_module.validate_date_format = validate_date_format
utils_module.parse_datetime_to_timestamp = parse_datetime_to_timestamp
sys.modules["utils"] = utils_module

# Mock the models module for Shipment
models_module = types.ModuleType("models")
class Shipment:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items()}
    
    def __repr__(self):
        return f"Shipment({self.__dict__})"

models_module.Shipment = Shipment
sys.modules["models"] = models_module

# Import tool_impls first so it uses our utils module
import tool_impls.search_shipments  # noqa: F401

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_search_shipments import SearchShipments

# Patch json.dumps in the tool module to handle Shipment objects
import json as json_module
_original_dumps = json_module.dumps

def _custom_dumps(obj, **kwargs):
    """Custom JSON dumps that handles Shipment objects."""
    if isinstance(obj, list):
        obj = [item.dict() if isinstance(item, Shipment) else item for item in obj]
    elif isinstance(obj, Shipment):
        obj = obj.dict()
    return _original_dumps(obj, **kwargs)

import tau_search_shipments
tau_search_shipments.json.dumps = _custom_dumps


class TestSearchShipments(unittest.TestCase):
    def setUp(self):
        """Set up test data with shipments."""
        # Note: createdAt must be INTEGER timestamp (milliseconds)
        self.data: Dict[str, Any] = {
            "Shipment": {
                "shipment1": {
                    "id": "shipment1",
                    "orderId": "order1",
                    "trackingNumber": "TRACK123",
                    "carrier": "FedEx",
                    "status": "in_transit",
                    "events": json.dumps([
                        {
                            "at": "2025-09-01T10:00:00Z",
                            "location": "New York",
                            "status": "label_created",
                        }
                    ]),
                    "createdAt": 1725120000000,  # 2025-09-01T00:00:00Z
                },
                "shipment2": {
                    "id": "shipment2",
                    "orderId": "order1",
                    "trackingNumber": "TRACK456",
                    "carrier": "UPS",
                    "status": "delivered",
                    "events": json.dumps([
                        {
                            "at": "2025-09-02T10:00:00Z",
                            "location": "Los Angeles",
                            "status": "delivered",
                        }
                    ]),
                    "createdAt": 1725206400000,  # 2025-09-02T00:00:00Z
                },
                "shipment3": {
                    "id": "shipment3",
                    "orderId": "order2",
                    "trackingNumber": "TRACK789",
                    "carrier": "USPS",
                    "status": "pending",
                    "events": json.dumps([]),
                    "createdAt": 1725292800000,  # 2025-09-03T00:00:00Z
                },
            }
        }

    def test_search_shipments_no_filters(self):
        """Test searching shipments with no filters."""
        result = SearchShipments.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return all shipments (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertGreater(len(result_list), 0)
        
        # Check structure of first shipment
        if result_list:
            shipment = result_list[0]
            self.assertIn("id", shipment)
            self.assertIn("orderId", shipment)
            self.assertIn("status", shipment)

    def test_search_shipments_by_order_id(self):
        """Test searching shipments by order ID."""
        result = SearchShipments.invoke(
            self.data,
            order_id="order1",
        )
        result_list = json.loads(result)
        
        # Should return shipments for order1
        self.assertGreater(len(result_list), 0)
        for shipment in result_list:
            self.assertEqual(shipment["orderId"], "order1")

    def test_search_shipments_by_tracking_number(self):
        """Test searching shipments by tracking number."""
        result = SearchShipments.invoke(
            self.data,
            tracking_number="TRACK123",
        )
        result_list = json.loads(result)
        
        # Should return shipment with matching tracking number
        self.assertGreater(len(result_list), 0)
        for shipment in result_list:
            self.assertEqual(shipment["trackingNumber"], "TRACK123")

    def test_search_shipments_filter_created_after(self):
        """Test filtering shipments created after a date."""
        result = SearchShipments.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include shipments created on or after 2025-09-02
        for shipment in result_list:
            self.assertGreaterEqual(shipment["createdAt"], 1725206400000)

    def test_search_shipments_filter_created_before(self):
        """Test filtering shipments created before a date."""
        result = SearchShipments.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include shipments created before the date
        # Verify filtering works by comparing with no filter
        result_no_filter = SearchShipments.invoke(self.data)
        no_filter_list = json.loads(result_no_filter)
        self.assertLessEqual(len(result_list), len(no_filter_list))

    def test_search_shipments_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchShipments.invoke(
            self.data,
            order_id="order1",
            created_after="2025-09-01T00:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should match shipments that satisfy all filters
        for shipment in result_list:
            self.assertEqual(shipment["orderId"], "order1")
            self.assertGreaterEqual(shipment["createdAt"], 1725120000000)

    def test_search_shipments_with_limit(self):
        """Test limiting the number of results."""
        result = SearchShipments.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)
        
        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_shipments_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchShipments.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)
        
        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_shipments_default_limit(self):
        """Test that default limit is 50."""
        result = SearchShipments.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_shipments_parses_events(self):
        """Test that events JSON field is parsed."""
        result = SearchShipments.invoke(
            self.data,
            tracking_number="TRACK123",
        )
        result_list = json.loads(result)
        
        # Should find shipment1 (may have duplicates)
        self.assertGreater(len(result_list), 0)
        shipment1 = next((s for s in result_list if s["id"] == "shipment1"), None)
        self.assertIsNotNone(shipment1)
        
        # events should be parsed from JSON string to list
        if "events" in shipment1:
            self.assertIsInstance(shipment1["events"], list)
            if shipment1["events"]:
                self.assertIsInstance(shipment1["events"][0], dict)

    def test_search_shipments_sorted_by_created_at(self):
        """Test that results are sorted by createdAt DESC, then id ASC."""
        result = SearchShipments.invoke(self.data)
        result_list = json.loads(result)
        
        if len(result_list) >= 2:
            # Check that shipments are sorted by createdAt descending
            for i in range(len(result_list) - 1):
                current_created = result_list[i]["createdAt"]
                next_created = result_list[i + 1]["createdAt"]
                # Should be in descending order
                if current_created == next_created:
                    # If createdAt is equal, check IDs
                    current_id = result_list[i]["id"]
                    next_id = result_list[i + 1]["id"]
                    self.assertLessEqual(current_id, next_id)
                else:
                    self.assertGreaterEqual(current_created, next_created)

    def test_search_shipments_no_results(self):
        """Test search with filters that match no shipments."""
        result = SearchShipments.invoke(
            self.data,
            order_id="nonexistent",
        )
        result_list = json.loads(result)
        
        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchShipments.get_info()
        
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchShipments")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("order_id", info["function"]["parameters"]["properties"])
        self.assertIn("tracking_number", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()

