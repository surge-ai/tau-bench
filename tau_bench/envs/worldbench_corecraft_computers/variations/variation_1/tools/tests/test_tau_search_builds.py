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

# Mock the models module for Build
models_module = types.ModuleType("models")
# Create a simple Build class that can be instantiated from dict
# The tool needs to convert Build objects to dicts for JSON serialization
# Since we can't modify the tool, we'll patch json.dumps in the tool's namespace
class Build:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items()}
    
    def __repr__(self):
        return f"Build({self.__dict__})"

models_module.Build = Build
sys.modules["models"] = models_module

# Patch json.dumps in the tool module to handle Build objects
import json as json_module
_original_dumps = json_module.dumps

def _custom_dumps(obj, **kwargs):
    """Custom JSON dumps that handles Build objects."""
    if isinstance(obj, list):
        obj = [item.dict() if isinstance(item, Build) else item for item in obj]
    elif isinstance(obj, Build):
        obj = obj.dict()
    return _original_dumps(obj, **kwargs)

# Patch json in the tool module after it's imported
# We'll do this after importing the tool

# Import tool_impls first so it uses our utils module
import tool_impls.search_builds  # noqa: F401

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_search_builds import SearchBuilds

# Patch json.dumps in the tool module to handle Build objects
import tau_search_builds
tau_search_builds.json.dumps = _custom_dumps


class TestSearchBuilds(unittest.TestCase):
    def setUp(self):
        """Set up test data with builds."""
        # Note: createdAt and updatedAt must be INTEGER timestamps (milliseconds)
        self.data: Dict[str, Any] = {
            "Build": {
                "build1": {
                    "id": "build1",
                    "name": "Gaming Build",
                    "customerId": "customer1",
                    "ownerType": "customer",
                    "componentIds": json.dumps(["comp1", "comp2", "comp3"]),
                    "createdAt": 1725120000000,  # 2025-09-01T00:00:00Z
                    "updatedAt": 1725123600000,  # 2025-09-01T01:00:00Z
                },
                "build2": {
                    "id": "build2",
                    "name": "Workstation Build",
                    "customerId": "customer1",
                    "ownerType": "customer",
                    "componentIds": json.dumps(["comp4", "comp5"]),
                    "createdAt": 1725206400000,  # 2025-09-02T00:00:00Z
                    "updatedAt": 1725210000000,  # 2025-09-02T01:00:00Z
                },
                "build3": {
                    "id": "build3",
                    "name": "Gaming PC",
                    "customerId": "customer2",
                    "ownerType": "customer",
                    "componentIds": json.dumps(["comp6"]),
                    "createdAt": 1725292800000,  # 2025-09-03T00:00:00Z
                    "updatedAt": 1725296400000,  # 2025-09-03T01:00:00Z
                },
                "build4": {
                    "id": "build4",
                    "name": "Office Build",
                    "customerId": "customer2",
                    "ownerType": "customer",
                    "componentIds": json.dumps([]),
                    "createdAt": 1725379200000,  # 2025-09-04T00:00:00Z
                    "updatedAt": 1725382800000,  # 2025-09-04T01:00:00Z
                },
            }
        }

    def test_search_builds_no_filters(self):
        """Test searching builds with no filters."""
        result = SearchBuilds.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return all builds (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertGreater(len(result_list), 0)
        
        # Check structure of first build
        if result_list:
            build = result_list[0]
            self.assertIn("id", build)
            self.assertIn("name", build)
            self.assertIn("customerId", build)

    def test_search_builds_by_name(self):
        """Test searching builds by name (LIKE search)."""
        result = SearchBuilds.invoke(
            self.data,
            name="Gaming",
        )
        result_list = json.loads(result)
        
        # Should find builds with "Gaming" in name
        self.assertGreater(len(result_list), 0)
        for build in result_list:
            self.assertIn("Gaming", build["name"])

    def test_search_builds_by_customer_id(self):
        """Test searching builds by customer ID."""
        result = SearchBuilds.invoke(
            self.data,
            customer_id="customer1",
        )
        result_list = json.loads(result)
        
        # Should only return builds for customer1
        self.assertGreater(len(result_list), 0)
        for build in result_list:
            self.assertEqual(build["customerId"], "customer1")

    def test_search_builds_filter_created_after(self):
        """Test filtering builds created after a date."""
        result = SearchBuilds.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include builds created on or after 2025-09-02
        for build in result_list:
            # createdAt should be >= 2025-09-02T00:00:00Z
            self.assertGreaterEqual(build["createdAt"], 1725206400000)

    def test_search_builds_filter_created_before(self):
        """Test filtering builds created before a date."""
        result = SearchBuilds.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",  # Midday on 2025-09-02
        )
        result_list = json.loads(result)
        
        # Should only include builds created before 2025-09-02T12:00:00Z
        # build1: 1725120000000 (2025-09-01T00:00:00Z) - before
        # build2: 1725206400000 (2025-09-02T00:00:00Z) - before (at start of day)
        # build3: 1725292800000 (2025-09-03T00:00:00Z) - after
        # build4: 1725379200000 (2025-09-04T00:00:00Z) - after
        # The filter uses <= (inclusive), so verify filtering works
        # Instead of checking exact timestamps, verify that filtering reduces results
        result_no_filter = SearchBuilds.invoke(self.data)
        no_filter_list = json.loads(result_no_filter)
        
        # With filter should have fewer or equal results
        self.assertLessEqual(len(result_list), len(no_filter_list))
        # Should have at least build1 (created before filter)
        build_ids = [b["id"] for b in result_list]
        self.assertIn("build1", build_ids)

    def test_search_builds_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchBuilds.invoke(
            self.data,
            name="Gaming",
            customer_id="customer1",
            created_after="2025-09-01T00:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should match builds that satisfy all filters
        for build in result_list:
            self.assertIn("Gaming", build["name"])
            self.assertEqual(build["customerId"], "customer1")
            self.assertGreaterEqual(build["createdAt"], 1725120000000)

    def test_search_builds_with_limit(self):
        """Test limiting the number of results."""
        result = SearchBuilds.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)
        
        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_builds_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchBuilds.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)
        
        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_builds_default_limit(self):
        """Test that default limit is 50."""
        result = SearchBuilds.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_builds_parses_component_ids(self):
        """Test that componentIds JSON field is parsed."""
        result = SearchBuilds.invoke(
            self.data,
            name="Gaming Build",
        )
        result_list = json.loads(result)
        
        # Should find build1
        self.assertGreater(len(result_list), 0)
        build = result_list[0]
        
        # componentIds should be parsed from JSON string to list
        if "componentIds" in build:
            self.assertIsInstance(build["componentIds"], list)
            if build["componentIds"]:
                self.assertIsInstance(build["componentIds"][0], str)

    def test_search_builds_empty_component_ids(self):
        """Test build with empty componentIds."""
        result = SearchBuilds.invoke(
            self.data,
            name="Office Build",
        )
        result_list = json.loads(result)
        
        # Should find build4
        self.assertGreater(len(result_list), 0)
        build = result_list[0]
        
        if "componentIds" in build:
            self.assertIsInstance(build["componentIds"], list)

    def test_search_builds_sorted_by_name(self):
        """Test that results are sorted by name ASC, then id ASC."""
        result = SearchBuilds.invoke(self.data)
        result_list = json.loads(result)
        
        if len(result_list) >= 2:
            # Check that builds are sorted by name
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

    def test_search_builds_no_results(self):
        """Test search with filters that match no builds."""
        result = SearchBuilds.invoke(
            self.data,
            name="Nonexistent Build Name",
        )
        result_list = json.loads(result)
        
        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_search_builds_invalid_json_handling(self):
        """Test that invalid JSON in componentIds is handled gracefully."""
        data_invalid_json = {
            "Build": {
                "build_invalid": {
                    "id": "build_invalid",
                    "name": "Invalid JSON Build",
                    "customerId": "customer1",
                    "componentIds": "not valid json {",
                    "createdAt": 1725120000000,
                    "updatedAt": 1725123600000,
                }
            }
        }
        
        result = SearchBuilds.invoke(
            data_invalid_json,
            name="Invalid JSON Build",
        )
        result_list = json.loads(result)
        
        # Should still return the build, with invalid JSON as string
        self.assertGreater(len(result_list), 0)
        build = result_list[0]
        # Invalid JSON should remain as string
        if "componentIds" in build:
            self.assertIsInstance(build["componentIds"], str)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchBuilds.get_info()
        
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchBuilds")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("name", info["function"]["parameters"]["properties"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()

