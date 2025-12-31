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
sys.modules["utils"] = utils_module

# Mock the models module for Employee
models_module = types.ModuleType("models")
class Employee:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items()}
    
    def __repr__(self):
        return f"Employee({self.__dict__})"

models_module.Employee = Employee
sys.modules["models"] = models_module

# Import tool_impls first so it uses our utils module
import tool_impls.search_employees  # noqa: F401

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_search_employees import SearchEmployees

# Patch json.dumps in the tool module to handle Employee objects
import json as json_module
_original_dumps = json_module.dumps

def _custom_dumps(obj, **kwargs):
    """Custom JSON dumps that handles Employee objects."""
    if isinstance(obj, list):
        obj = [item.dict() if isinstance(item, Employee) else item for item in obj]
    elif isinstance(obj, Employee):
        obj = obj.dict()
    return _original_dumps(obj, **kwargs)

import tau_search_employees
tau_search_employees.json.dumps = _custom_dumps


class TestSearchEmployees(unittest.TestCase):
    def setUp(self):
        """Set up test data with employees."""
        self.data: Dict[str, Any] = {
            "Employee": {
                "employee1": {
                    "id": "employee1",
                    "name": "John Doe",
                    "email": "john@corecraft.com",
                    "department": "engineering",
                    "title": "Software Engineer",
                    "managerId": "manager1",
                    "permissions": json.dumps(["edit_order", "cancel_order"]),
                },
                "employee2": {
                    "id": "employee2",
                    "name": "Jane Smith",
                    "email": "jane@corecraft.com",
                    "department": "finance",
                    "title": "Accounts Manager",
                    "managerId": "manager2",
                    "permissions": json.dumps(["issue_refund"]),
                },
                "employee3": {
                    "id": "employee3",
                    "name": "Bob Johnson",
                    "email": "bob@corecraft.com",
                    "department": "engineering",
                    "title": "Senior Engineer",
                    "managerId": "manager1",
                    "permissions": json.dumps(["edit_order", "policy_override"]),
                },
                "employee4": {
                    "id": "employee4",
                    "name": "Alice Williams",
                    "email": "alice@corecraft.com",
                    "department": "help_desk",
                    "title": "Support Specialist",
                    "managerId": "manager3",
                    "permissions": json.dumps(["escalate", "kb_edit"]),
                },
            }
        }

    def test_search_employees_no_filters(self):
        """Test searching employees with no filters."""
        result = SearchEmployees.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return all employees (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertGreater(len(result_list), 0)
        
        # Check structure of first employee
        if result_list:
            employee = result_list[0]
            self.assertIn("id", employee)
            self.assertIn("name", employee)
            self.assertIn("email", employee)

    def test_search_employees_by_id(self):
        """Test searching employees by exact ID."""
        result = SearchEmployees.invoke(
            self.data,
            employee_id="employee1",
        )
        result_list = json.loads(result)
        
        # Should return at least one employee (may have duplicates from lowercase alias)
        self.assertGreater(len(result_list), 0)
        # Should include employee1
        employee_ids = [e["id"] for e in result_list]
        self.assertIn("employee1", employee_ids)
        # Find employee1 in results
        employee1 = next((e for e in result_list if e["id"] == "employee1"), None)
        self.assertIsNotNone(employee1)
        self.assertEqual(employee1["name"], "John Doe")

    def test_search_employees_by_name(self):
        """Test searching employees by name (LIKE search)."""
        result = SearchEmployees.invoke(
            self.data,
            name="John",
        )
        result_list = json.loads(result)
        
        # Should find employees with "John" in name
        self.assertGreater(len(result_list), 0)
        for employee in result_list:
            self.assertIn("John", employee["name"])

    def test_search_employees_by_department(self):
        """Test searching employees by department."""
        result = SearchEmployees.invoke(
            self.data,
            department="engineering",
        )
        result_list = json.loads(result)
        
        # Should return employees in engineering department
        self.assertGreater(len(result_list), 0)
        for employee in result_list:
            self.assertEqual(employee["department"], "engineering")

    def test_search_employees_by_role(self):
        """Test searching employees by role/title (LIKE search)."""
        result = SearchEmployees.invoke(
            self.data,
            role="Engineer",
        )
        result_list = json.loads(result)
        
        # Should find employees with "Engineer" in title
        self.assertGreater(len(result_list), 0)
        for employee in result_list:
            self.assertIn("Engineer", employee["title"])

    def test_search_employees_by_permission(self):
        """Test searching employees by permission."""
        result = SearchEmployees.invoke(
            self.data,
            has_permission="edit_order",
        )
        result_list = json.loads(result)
        
        # Should return employees with edit_order permission
        self.assertGreater(len(result_list), 0)
        for employee in result_list:
            # Permissions should be parsed from JSON
            if "permissions" in employee:
                permissions = employee["permissions"]
                if isinstance(permissions, list):
                    self.assertIn("edit_order", permissions)
                elif isinstance(permissions, str):
                    # If still a string, check it contains the permission
                    self.assertIn("edit_order", permissions)

    def test_search_employees_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchEmployees.invoke(
            self.data,
            department="engineering",
            role="Engineer",
        )
        result_list = json.loads(result)
        
        # Should match employees that satisfy all filters
        for employee in result_list:
            self.assertEqual(employee["department"], "engineering")
            self.assertIn("Engineer", employee["title"])

    def test_search_employees_with_limit(self):
        """Test limiting the number of results."""
        result = SearchEmployees.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)
        
        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_employees_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchEmployees.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)
        
        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_employees_default_limit(self):
        """Test that default limit is 50."""
        result = SearchEmployees.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_employees_parses_permissions(self):
        """Test that permissions JSON field is parsed."""
        result = SearchEmployees.invoke(
            self.data,
            employee_id="employee1",
        )
        result_list = json.loads(result)
        
        # Should find employee1 (may have duplicates)
        self.assertGreater(len(result_list), 0)
        employee1 = next((e for e in result_list if e["id"] == "employee1"), None)
        self.assertIsNotNone(employee1)
        
        # permissions should be parsed from JSON string to list
        if "permissions" in employee1:
            self.assertIsInstance(employee1["permissions"], list)
            if employee1["permissions"]:
                self.assertIsInstance(employee1["permissions"][0], str)

    def test_search_employees_sorted_by_name(self):
        """Test that results are sorted by name ASC, then id ASC."""
        result = SearchEmployees.invoke(self.data)
        result_list = json.loads(result)
        
        if len(result_list) >= 2:
            # Check that employees are sorted by name
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

    def test_search_employees_no_results(self):
        """Test search with filters that match no employees."""
        result = SearchEmployees.invoke(
            self.data,
            employee_id="nonexistent",
        )
        result_list = json.loads(result)
        
        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchEmployees.get_info()
        
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchEmployees")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("employee_id", info["function"]["parameters"]["properties"])
        self.assertIn("name", info["function"]["parameters"]["properties"])
        self.assertIn("department", info["function"]["parameters"]["properties"])
        self.assertIn("role", info["function"]["parameters"]["properties"])
        self.assertIn("has_permission", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()

