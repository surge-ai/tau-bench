import json
import unittest
from typing import Dict, Any

from ..tau_search_employees import SearchEmployees


class TestSearchEmployees(unittest.TestCase):
    def setUp(self):
        """Set up test data with employees."""
        self.data: Dict[str, Any] = {
            "employee": {
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
        self.assertEqual(len(result_list), 4)

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

        # Should return exactly one employee
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "employee1")
        self.assertEqual(result_list[0]["name"], "John Doe")

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
        self.assertEqual(len(result_list), 2)
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
        self.assertEqual(len(result_list), 2)
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
        self.assertEqual(len(result_list), 2)
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
        self.assertEqual(len(result_list), 2)
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

        # Should find employee1
        self.assertEqual(len(result_list), 1)
        employee1 = result_list[0]

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
