import json
import unittest
from typing import Dict, Any

from ..tau_search_builds import SearchBuilds


class TestSearchBuilds(unittest.TestCase):
    def setUp(self):
        """Set up test data with builds."""
        self.data: Dict[str, Any] = {
            "build": {
                "build1": {
                    "id": "build1",
                    "name": "Gaming PC Build",
                    "customerId": "customer1",
                    "componentIds": json.dumps(["cpu1", "gpu1", "ram1"]),
                    "createdAt": "2025-09-01T00:00:00Z",
                },
                "build2": {
                    "id": "build2",
                    "name": "Workstation Build",
                    "customerId": "customer1",
                    "componentIds": json.dumps(["cpu2", "gpu2", "ram2"]),
                    "createdAt": "2025-09-02T00:00:00Z",
                },
                "build3": {
                    "id": "build3",
                    "name": "Budget Gaming PC",
                    "customerId": "customer2",
                    "componentIds": json.dumps(["cpu3", "ram3"]),
                    "createdAt": "2025-09-03T00:00:00Z",
                },
            }
        }

    def test_search_builds_no_filters(self):
        """Test searching builds with no filters."""
        result = SearchBuilds.invoke(self.data)
        result_list = result

        # Should return all builds (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 3)

        # Check structure of first build
        if result_list:
            build = result_list[0]
            self.assertIn("id", build)
            self.assertIn("name", build)
            self.assertIn("customerId", build)

    def test_search_builds_by_name(self):
        """Test searching builds by name (partial match)."""
        result = SearchBuilds.invoke(
            self.data,
            name="Gaming",
        )
        result_list = result

        # Should find builds with "Gaming" in name
        self.assertEqual(len(result_list), 2)
        for build in result_list:
            self.assertIn("Gaming", build["name"])

    def test_search_builds_by_customer_id(self):
        """Test searching builds by customer ID."""
        result = SearchBuilds.invoke(
            self.data,
            customer_id="customer1",
        )
        result_list = result

        # Should return builds for customer1
        self.assertEqual(len(result_list), 2)
        for build in result_list:
            self.assertEqual(build["customerId"], "customer1")

    def test_search_builds_filter_created_after(self):
        """Test filtering builds created after a date."""
        result = SearchBuilds.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = result

        # Should only include builds created on or after 2025-09-02
        self.assertEqual(len(result_list), 2)
        for build in result_list:
            self.assertGreaterEqual(build["createdAt"], "2025-09-02T00:00:00Z")

    def test_search_builds_filter_created_before(self):
        """Test filtering builds created before a date."""
        result = SearchBuilds.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )
        result_list = result

        # Should only include builds created before the date
        self.assertEqual(len(result_list), 2)
        for build in result_list:
            self.assertLess(build["createdAt"], "2025-09-02T12:00:00Z")

    def test_search_builds_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchBuilds.invoke(
            self.data,
            name="Gaming",
            customer_id="customer1",
            created_after="2025-09-01T00:00:00Z",
        )
        result_list = result

        # Should match builds that satisfy all filters
        # - name="Gaming": matches build1, build3 (2 builds)
        # - customer_id="customer1": matches build1, build2 (2 builds)
        # - created_after="2025-09-01": matches build1, build2, build3 (3 builds)
        # Combined: only build1 matches all three
        self.assertEqual(len(result_list), 1)
        for build in result_list:
            self.assertIn("Gaming", build["name"])
            self.assertEqual(build["customerId"], "customer1")
            self.assertGreaterEqual(build["createdAt"], "2025-09-01T00:00:00Z")

    def test_search_builds_with_limit(self):
        """Test limiting the number of results."""
        result = SearchBuilds.invoke(
            self.data,
            limit=2,
        )
        result_list = result

        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_builds_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchBuilds.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = result

        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_builds_default_limit(self):
        """Test that default limit is 50."""
        result = SearchBuilds.invoke(self.data)
        result_list = result

        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_builds_parses_component_ids(self):
        """Test that componentIds JSON field is parsed."""
        result = SearchBuilds.invoke(
            self.data,
            name="Gaming PC Build",
        )
        result_list = result

        # Should find build1
        self.assertGreater(len(result_list), 0)
        build1 = result_list[0]

        # componentIds should be parsed from JSON string to list
        if "componentIds" in build1:
            self.assertIsInstance(build1["componentIds"], list)
            if build1["componentIds"]:
                self.assertIsInstance(build1["componentIds"][0], str)

    def test_search_builds_empty_component_ids(self):
        """Test build with empty componentIds."""
        # Add a build with empty componentIds
        data_with_empty = {
            "build": {
                "build_empty": {
                    "id": "build_empty",
                    "name": "Empty Build",
                    "customerId": "customer1",
                    "componentIds": json.dumps([]),
                    "createdAt": "2025-09-01T00:00:00Z",
                },
            }
        }
        result = SearchBuilds.invoke(
            data_with_empty,
            name="Empty Build",
        )
        result_list = result

        # Should find the build with empty componentIds
        self.assertEqual(len(result_list), 1)
        build = result_list[0]
        self.assertEqual(build["id"], "build_empty")
        self.assertIn("componentIds", build)
        self.assertIsInstance(build["componentIds"], list)
        self.assertEqual(len(build["componentIds"]), 0)

    def test_search_builds_sorted_by_name(self):
        """Test that results are sorted by name ASC, then id ASC."""
        result = SearchBuilds.invoke(self.data)
        result_list = result

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
            customer_id="nonexistent",
        )
        result_list = result

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_search_builds_invalid_json_handling(self):
        """Test that invalid JSON in componentIds is handled gracefully."""
        data_invalid_json = {
            "build": {
                "build_invalid": {
                    "id": "build_invalid",
                    "name": "Invalid JSON Build",
                    "customerId": "customer1",
                    "componentIds": "not valid json {",
                    "createdAt": "2025-09-01T00:00:00Z",
                },
            }
        }

        result = SearchBuilds.invoke(
            data_invalid_json,
            name="Invalid JSON Build",
        )
        result_list = result

        # Should still return the build, with invalid JSON kept as string
        self.assertEqual(len(result_list), 1)
        build = result_list[0]
        self.assertEqual(build["id"], "build_invalid")
        # Invalid JSON should remain as string (not parsed)
        self.assertIn("componentIds", build)
        self.assertIsInstance(build["componentIds"], str)
        self.assertEqual(build["componentIds"], "not valid json {")

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
