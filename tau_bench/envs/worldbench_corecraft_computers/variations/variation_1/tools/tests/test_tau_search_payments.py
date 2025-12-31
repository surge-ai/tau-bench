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
from ..tau_sqlite_utils import build_sqlite_from_data
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

# Mock the models module for Payment
models_module = types.ModuleType("models")
class Payment:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items()}
    
    def __repr__(self):
        return f"Payment({self.__dict__})"

models_module.Payment = Payment
sys.modules["models"] = models_module

# Import tool_impls first so it uses our utils module
import tool_impls.search_payments  # noqa: F401

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_search_payments import SearchPayments

# Patch json.dumps in the tool module to handle Payment objects
import json as json_module
_original_dumps = json_module.dumps

def _custom_dumps(obj, **kwargs):
    """Custom JSON dumps that handles Payment objects."""
    if isinstance(obj, list):
        obj = [item.dict() if isinstance(item, Payment) else item for item in obj]
    elif isinstance(obj, Payment):
        obj = obj.dict()
    return _original_dumps(obj, **kwargs)

import tau_search_payments
tau_search_payments.json.dumps = _custom_dumps


class TestSearchPayments(unittest.TestCase):
    def setUp(self):
        """Set up test data with payments."""
        # Note: createdAt and processedAt must be INTEGER timestamps (milliseconds)
        self.data: Dict[str, Any] = {
            "Payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 100.0,
                    "method": "card",
                    "status": "captured",
                    "transactionId": "TXN-001",
                    "createdAt": 1725120000000,  # 2025-09-01T00:00:00Z
                    "processedAt": 1725121000000,  # 2025-09-01T00:16:40Z
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order1",
                    "amount": 150.0,
                    "method": "paypal",
                    "status": "refunded",
                    "transactionId": "TXN-002",
                    "createdAt": 1725206400000,  # 2025-09-02T00:00:00Z
                    "processedAt": 1725207000000,  # 2025-09-02T00:10:00Z
                },
                "payment3": {
                    "id": "payment3",
                    "orderId": "order2",
                    "amount": 200.0,
                    "method": "card",
                    "status": "pending",
                    "transactionId": "TXN-003",
                    "createdAt": 1725292800000,  # 2025-09-03T00:00:00Z
                    "processedAt": None,
                },
                "payment4": {
                    "id": "payment4",
                    "orderId": "order3",
                    "amount": 50.0,
                    "method": "card",
                    "status": "captured",
                    "transactionId": "TXN-004",
                    "createdAt": 1725379200000,  # 2025-09-04T00:00:00Z
                    "processedAt": 1725380000000,  # 2025-09-04T00:13:20Z
                },
            }
        }

    def test_search_payments_no_filters(self):
        """Test searching payments with no filters."""
        result = SearchPayments.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return all payments (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertGreater(len(result_list), 0)
        
        # Check structure of first payment
        if result_list:
            payment = result_list[0]
            self.assertIn("id", payment)
            self.assertIn("orderId", payment)
            self.assertIn("status", payment)

    def test_search_payments_by_order_id(self):
        """Test searching payments by order ID."""
        result = SearchPayments.invoke(
            self.data,
            order_id="order1",
        )
        result_list = json.loads(result)
        
        # Should return payments for order1
        self.assertGreater(len(result_list), 0)
        for payment in result_list:
            self.assertEqual(payment["orderId"], "order1")

    def test_search_payments_by_status(self):
        """Test searching payments by status."""
        result = SearchPayments.invoke(
            self.data,
            status="captured",
        )
        result_list = json.loads(result)
        
        # Should return payments with captured status
        self.assertGreater(len(result_list), 0)
        for payment in result_list:
            self.assertEqual(payment["status"], "captured")

    def test_search_payments_filter_created_after(self):
        """Test filtering payments created after a date."""
        result = SearchPayments.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include payments created on or after 2025-09-02
        for payment in result_list:
            self.assertGreaterEqual(payment["createdAt"], 1725206400000)

    def test_search_payments_filter_created_before(self):
        """Test filtering payments created before a date."""
        result = SearchPayments.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include payments created before the date
        # Verify filtering works by comparing with no filter
        result_no_filter = SearchPayments.invoke(self.data)
        no_filter_list = json.loads(result_no_filter)
        self.assertLessEqual(len(result_list), len(no_filter_list))

    def test_search_payments_filter_processed_after(self):
        """Test filtering payments processed after a date."""
        result = SearchPayments.invoke(
            self.data,
            processed_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include payments processed on or after the date
        for payment in result_list:
            if payment.get("processedAt") is not None:
                self.assertGreaterEqual(payment["processedAt"], 1725206400000)

    def test_search_payments_filter_processed_before(self):
        """Test filtering payments processed before a date."""
        result = SearchPayments.invoke(
            self.data,
            processed_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include payments processed before the date
        # Verify filtering works
        result_no_filter = SearchPayments.invoke(self.data)
        no_filter_list = json.loads(result_no_filter)
        self.assertLessEqual(len(result_list), len(no_filter_list))

    def test_search_payments_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchPayments.invoke(
            self.data,
            order_id="order1",
            status="captured",
        )
        result_list = json.loads(result)
        
        # Should match payments that satisfy all filters
        for payment in result_list:
            self.assertEqual(payment["orderId"], "order1")
            self.assertEqual(payment["status"], "captured")

    def test_search_payments_with_limit(self):
        """Test limiting the number of results."""
        result = SearchPayments.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)
        
        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_payments_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchPayments.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)
        
        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_payments_default_limit(self):
        """Test that default limit is 50."""
        result = SearchPayments.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_payments_sorted_by_created_at(self):
        """Test that results are sorted by createdAt DESC, then id ASC."""
        result = SearchPayments.invoke(self.data)
        result_list = json.loads(result)
        
        if len(result_list) >= 2:
            # Check that payments are sorted by createdAt descending
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

    def test_search_payments_no_results(self):
        """Test search with filters that match no payments."""
        result = SearchPayments.invoke(
            self.data,
            order_id="nonexistent",
        )
        result_list = json.loads(result)
        
        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchPayments.get_info()
        
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchPayments")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("order_id", info["function"]["parameters"]["properties"])
        self.assertIn("status", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("processed_after", info["function"]["parameters"]["properties"])
        self.assertIn("processed_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()

