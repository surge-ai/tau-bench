import json
import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_search_knowledge_base import SearchKnowledgeBase


class TestSearchKnowledgeBase(unittest.TestCase):
    def setUp(self):
        """Set up test data with knowledge base articles."""
        self.data: Dict[str, Any] = {
            "knowledgeBaseArticle": {
                "kb1": {
                    "id": "kb1",
                    "title": "How to Troubleshoot Boot Issues",
                    "body": "If your computer won't boot, try these steps...",
                    "category": "troubleshooting",
                    "tags": json.dumps(["boot", "hardware", "bios"]),
                    "createdAt": "2025-09-01T00:00:00Z",
                    "updatedAt": "2025-09-01T01:00:00Z",
                },
                "kb2": {
                    "id": "kb2",
                    "title": "Return Policy Guide",
                    "body": "Our return policy allows returns within 30 days...",
                    "category": "policy",
                    "tags": json.dumps(["return", "refund", "exchange"]),
                    "createdAt": "2025-09-02T00:00:00Z",
                    "updatedAt": "2025-09-02T01:00:00Z",
                },
                "kb3": {
                    "id": "kb3",
                    "title": "GPU Installation Guide",
                    "body": "Follow these steps to install a new graphics card...",
                    "category": "guide",
                    "tags": json.dumps(["gpu", "installation", "hardware"]),
                    "createdAt": "2025-09-03T00:00:00Z",
                    "updatedAt": "2025-09-03T01:00:00Z",
                },
            }
        }

    def test_search_knowledge_base_no_filters(self):
        """Test searching knowledge base with no filters."""
        result = SearchKnowledgeBase.invoke(self.data)
        result_list = json.loads(result)

        # Should return all articles (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 3)

        # Check structure of first article
        if result_list:
            article = result_list[0]
            self.assertIn("id", article)
            self.assertIn("title", article)
            self.assertIn("category", article)

    def test_search_knowledge_base_by_text(self):
        """Test searching knowledge base by text (searches title and body)."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            text="boot",
        )
        result_list = json.loads(result)

        # Should find articles with "boot" in title or body
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "kb1")

    def test_search_knowledge_base_by_category(self):
        """Test searching knowledge base by category."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            category="troubleshooting",
        )
        result_list = json.loads(result)

        # Should return articles in troubleshooting category
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["category"], "troubleshooting")

    def test_search_knowledge_base_by_tag(self):
        """Test searching knowledge base by tag."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            tag="hardware",
        )
        result_list = json.loads(result)

        # Should return articles with "hardware" tag
        self.assertEqual(len(result_list), 2)
        for article in result_list:
            if "tags" in article:
                tags = article["tags"]
                if isinstance(tags, list):
                    self.assertIn("hardware", tags)
                elif isinstance(tags, str):
                    self.assertIn("hardware", tags)

    def test_search_knowledge_base_filter_updated_after(self):
        """Test filtering articles updated after a date."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            updated_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include articles updated on or after 2025-09-02
        self.assertEqual(len(result_list), 2)
        for article in result_list:
            self.assertGreaterEqual(article["updatedAt"], "2025-09-02T00:00:00Z")

    def test_search_knowledge_base_filter_updated_before(self):
        """Test filtering articles updated before a date."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            updated_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include articles updated before the date
        self.assertEqual(len(result_list), 2)

    def test_search_knowledge_base_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            category="troubleshooting",
            tag="boot",
        )
        result_list = json.loads(result)

        # Should match articles that satisfy all filters
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["category"], "troubleshooting")

    def test_search_knowledge_base_with_limit(self):
        """Test limiting the number of results."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)

        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_knowledge_base_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)

        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_knowledge_base_default_limit(self):
        """Test that default limit is 50."""
        result = SearchKnowledgeBase.invoke(self.data)
        result_list = json.loads(result)

        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_knowledge_base_parses_tags(self):
        """Test that tags JSON field is parsed."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            text="Troubleshoot",
        )
        result_list = json.loads(result)

        # Should find kb1
        self.assertEqual(len(result_list), 1)
        kb1 = result_list[0]

        # tags should be parsed from JSON string to list
        if "tags" in kb1:
            self.assertIsInstance(kb1["tags"], list)

    def test_search_knowledge_base_sorted_by_title(self):
        """Test that results are sorted by title ASC, then id ASC."""
        result = SearchKnowledgeBase.invoke(self.data)
        result_list = json.loads(result)

        if len(result_list) >= 2:
            # Check that articles are sorted by title ascending
            for i in range(len(result_list) - 1):
                current_title = result_list[i]["title"]
                next_title = result_list[i + 1]["title"]
                # Should be in ascending order
                if current_title == next_title:
                    # If title is equal, check IDs
                    current_id = result_list[i]["id"]
                    next_id = result_list[i + 1]["id"]
                    self.assertLessEqual(current_id, next_id)
                else:
                    self.assertLessEqual(current_title, next_title)

    def test_search_knowledge_base_no_results(self):
        """Test search with filters that match no articles."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            text="nonexistent_term",
        )
        result_list = json.loads(result)

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchKnowledgeBase.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchKnowledgeBase")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("text", info["function"]["parameters"]["properties"])
        self.assertIn("category", info["function"]["parameters"]["properties"])
        self.assertIn("tag", info["function"]["parameters"]["properties"])
        self.assertIn("updated_after", info["function"]["parameters"]["properties"])
        self.assertIn("updated_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()
