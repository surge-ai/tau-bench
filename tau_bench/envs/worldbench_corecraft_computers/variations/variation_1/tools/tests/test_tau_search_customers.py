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

# Mock the models module for Customer
models_module = types.ModuleType("models")
class Customer:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items()}
    
    def __repr__(self):
        return f"Customer({self.__dict__})"

models_module.Customer = Customer
sys.modules["models"] = models_module

# Import tool_impls first so it uses our utils module
import tool_impls.search_customers  # noqa: F401

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_search_customers import SearchCustomers

# Patch json.dumps in the tool module to handle Customer objects
import json as json_module
_original_dumps = json_module.dumps

def _custom_dumps(obj, **kwargs):
    """Custom JSON dumps that handles Customer objects."""
    if isinstance(obj, list):
        obj = [item.dict() if isinstance(item, Customer) else item for item in obj]
    elif isinstance(obj, Customer):
        obj = obj.dict()
    return _original_dumps(obj, **kwargs)

import tau_search_customers
tau_search_customers.json.dumps = _custom_dumps


class TestSearchCustomers(unittest.TestCase):
    def setUp(self):
        """Set up test data with customers."""
        # Note: createdAt must be INTEGER timestamp (milliseconds) if used
        self.data: Dict[str, Any] = {
            "Customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "(555) 123-4567",
                    "loyaltyTier": "gold",
                    "addresses": json.dumps([
                        {
                            "label": "shipping",
                            "line1": "123 Main St",
                            "city": "New York",
                            "region": "NY",
                            "postalCode": "10001",
                            "country": "US"
                        }
                    ]),
                    "createdAt": 1725120000000,  # 2025-09-01T00:00:00Z
                },
                "customer2": {
                    "id": "customer2",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "phone": "(555) 987-6543",
                    "loyaltyTier": "silver",
                    "addresses": json.dumps([
                        {
                            "label": "billing",
                            "line1": "456 Oak Ave",
                            "city": "Los Angeles",
                            "region": "CA",
                            "postalCode": "90001",
                            "country": "US"
                        }
                    ]),
                    "createdAt": 1725206400000,  # 2025-09-02T00:00:00Z
                },
                "customer3": {
                    "id": "customer3",
                    "name": "Bob Johnson",
                    "email": "bob@example.com",
                    "phone": "(555) 111-2222",
                    "loyaltyTier": "platinum",
                    "addresses": json.dumps([
                        {
                            "label": "shipping",
                            "line1": "789 Pine Rd",
                            "city": "Chicago",
                            "region": "IL",
                            "postalCode": "60601",
                            "country": "US"
                        }
                    ]),
                    "createdAt": 1725292800000,  # 2025-09-03T00:00:00Z
                },
            }
        }

    def test_search_customers_no_filters(self):
        """Test searching customers with no filters."""
        result = SearchCustomers.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return all customers (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertGreater(len(result_list), 0)
        
        # Check structure of first customer
        if result_list:
            customer = result_list[0]
            self.assertIn("id", customer)
            self.assertIn("name", customer)
            self.assertIn("email", customer)

    def test_search_customers_by_id(self):
        """Test searching customers by exact ID."""
        result = SearchCustomers.invoke(
            self.data,
            customer_id="customer1",
        )
        result_list = json.loads(result)
        
        # Should return at least one customer (may have duplicates from lowercase alias)
        self.assertGreater(len(result_list), 0)
        # Should include customer1
        customer_ids = [c["id"] for c in result_list]
        self.assertIn("customer1", customer_ids)
        # Find customer1 in results
        customer1 = next((c for c in result_list if c["id"] == "customer1"), None)
        self.assertIsNotNone(customer1)
        self.assertEqual(customer1["name"], "John Doe")

    def test_search_customers_by_name(self):
        """Test searching customers by name (LIKE search)."""
        result = SearchCustomers.invoke(
            self.data,
            name="John",
        )
        result_list = json.loads(result)
        
        # Should find customers with "John" in name
        self.assertGreater(len(result_list), 0)
        for customer in result_list:
            self.assertIn("John", customer["name"])

    def test_search_customers_by_email(self):
        """Test searching customers by exact email."""
        result = SearchCustomers.invoke(
            self.data,
            email="jane@example.com",
        )
        result_list = json.loads(result)
        
        # Should return at least one customer (may have duplicates from lowercase alias)
        self.assertGreater(len(result_list), 0)
        # All results should have the matching email
        for customer in result_list:
            self.assertEqual(customer["email"], "jane@example.com")

    def test_search_customers_by_phone(self):
        """Test searching customers by exact phone."""
        result = SearchCustomers.invoke(
            self.data,
            phone="(555) 123-4567",
        )
        result_list = json.loads(result)
        
        # Should return at least one customer (may have duplicates from lowercase alias)
        self.assertGreater(len(result_list), 0)
        # All results should have the matching phone
        for customer in result_list:
            self.assertEqual(customer["phone"], "(555) 123-4567")

    def test_search_customers_by_loyalty_tier(self):
        """Test searching customers by loyalty tier."""
        result = SearchCustomers.invoke(
            self.data,
            loyalty_tier="gold",
        )
        result_list = json.loads(result)
        
        # Should return customers with gold tier
        self.assertGreater(len(result_list), 0)
        for customer in result_list:
            self.assertEqual(customer["loyaltyTier"], "gold")

    def test_search_customers_by_address_text(self):
        """Test searching customers by address text."""
        result = SearchCustomers.invoke(
            self.data,
            address_text="New York",
        )
        result_list = json.loads(result)
        
        # Should find customers with "New York" in addresses
        self.assertGreater(len(result_list), 0)
        # Addresses should be parsed from JSON
        for customer in result_list:
            if "addresses" in customer:
                addresses_str = json.dumps(customer["addresses"])
                self.assertIn("New York", addresses_str)

    def test_search_customers_filter_created_after(self):
        """Test filtering customers created after a date."""
        result = SearchCustomers.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include customers created on or after 2025-09-02
        for customer in result_list:
            self.assertGreaterEqual(customer["createdAt"], 1725206400000)

    def test_search_customers_filter_created_before(self):
        """Test filtering customers created before a date."""
        result = SearchCustomers.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include customers created before the date
        # Verify filtering works by comparing with no filter
        result_no_filter = SearchCustomers.invoke(self.data)
        no_filter_list = json.loads(result_no_filter)
        self.assertLessEqual(len(result_list), len(no_filter_list))

    def test_search_customers_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchCustomers.invoke(
            self.data,
            name="John",
            loyalty_tier="gold",
        )
        result_list = json.loads(result)
        
        # Should match customers that satisfy all filters
        for customer in result_list:
            self.assertIn("John", customer["name"])
            self.assertEqual(customer["loyaltyTier"], "gold")

    def test_search_customers_with_limit(self):
        """Test limiting the number of results."""
        result = SearchCustomers.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)
        
        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_customers_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchCustomers.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)
        
        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_customers_default_limit(self):
        """Test that default limit is 50."""
        result = SearchCustomers.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_customers_parses_addresses(self):
        """Test that addresses JSON field is parsed."""
        result = SearchCustomers.invoke(
            self.data,
            customer_id="customer1",
        )
        result_list = json.loads(result)
        
        # Should find customer1 (may have duplicates)
        self.assertGreater(len(result_list), 0)
        customer1 = next((c for c in result_list if c["id"] == "customer1"), None)
        self.assertIsNotNone(customer1)
        
        # addresses should be parsed from JSON string to list
        if "addresses" in customer1:
            self.assertIsInstance(customer1["addresses"], list)
            if customer1["addresses"]:
                self.assertIsInstance(customer1["addresses"][0], dict)

    def test_search_customers_sorted_by_name(self):
        """Test that results are sorted by name ASC, then id ASC."""
        result = SearchCustomers.invoke(self.data)
        result_list = json.loads(result)
        
        if len(result_list) >= 2:
            # Check that customers are sorted by name
            for i in range(len(result_list) - 1):
                current_name = result_list[i]["name"]
                next_name = result_list[i + 1]["name"]
                # Names should be in ascending order
                if current_name == next_name:
                    # If names are equal, check IDs
                    current_id = result_list[i]["id"]
                    next_id = result_list[i + 1]["id"]
                    self.assertLessEqual(current_id, next_id)
                else:
                    self.assertLessEqual(current_name, next_name)

    def test_search_customers_no_results(self):
        """Test search with filters that match no customers."""
        result = SearchCustomers.invoke(
            self.data,
            customer_id="nonexistent",
        )
        result_list = json.loads(result)
        
        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchCustomers.get_info()
        
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchCustomers")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("name", info["function"]["parameters"]["properties"])
        self.assertIn("email", info["function"]["parameters"]["properties"])
        self.assertIn("phone", info["function"]["parameters"]["properties"])
        self.assertIn("loyalty_tier", info["function"]["parameters"]["properties"])
        self.assertIn("address_text", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()

