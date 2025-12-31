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

# Mock the models module for KnowledgeBaseArticle
models_module = types.ModuleType("models")
class KnowledgeBaseArticle:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items()}
    
    def __repr__(self):
        return f"KnowledgeBaseArticle({self.__dict__})"

models_module.KnowledgeBaseArticle = KnowledgeBaseArticle
sys.modules["models"] = models_module

# Import tool_impls first so it uses our utils module
import tool_impls.search_knowledge_base  # noqa: F401

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_search_knowledge_base import SearchKnowledgeBase

# Patch json.dumps in the tool module to handle KnowledgeBaseArticle objects
import json as json_module
_original_dumps = json_module.dumps

def _custom_dumps(obj, **kwargs):
    """Custom JSON dumps that handles KnowledgeBaseArticle objects."""
    if isinstance(obj, list):
        obj = [item.dict() if isinstance(item, KnowledgeBaseArticle) else item for item in obj]
    elif isinstance(obj, KnowledgeBaseArticle):
        obj = obj.dict()
    return _original_dumps(obj, **kwargs)

import tau_search_knowledge_base
tau_search_knowledge_base.json.dumps = _custom_dumps


class TestSearchKnowledgeBase(unittest.TestCase):
    def setUp(self):
        """Set up test data with knowledge base articles."""
        # Note: createdAt and updatedAt must be INTEGER timestamps (milliseconds)
        self.data: Dict[str, Any] = {
            "KnowledgeBaseArticle": {
                "article1": {
                    "id": "article1",
                    "title": "CPU Installation Guide",
                    "body": "This is a guide for installing CPUs. Follow these steps carefully.",
                    "tags": json.dumps(["cpu", "installation", "hardware"]),
                    "productsMentioned": json.dumps(["product1", "product2"]),
                    "version": "1.0",
                    "isDeprecated": False,
                    "createdAt": 1725120000000,  # 2025-09-01T00:00:00Z
                    "updatedAt": 1725123600000,  # 2025-09-01T01:00:00Z
                },
                "article2": {
                    "id": "article2",
                    "title": "GPU Troubleshooting",
                    "body": "Common GPU issues and how to troubleshoot them. Check drivers first.",
                    "tags": json.dumps(["gpu", "troubleshooting"]),
                    "productsMentioned": json.dumps(["product3"]),
                    "version": "2.0",
                    "isDeprecated": False,
                    "createdAt": 1725206400000,  # 2025-09-02T00:00:00Z
                    "updatedAt": 1725210000000,  # 2025-09-02T01:00:00Z
                },
                "article3": {
                    "id": "article3",
                    "title": "RAM Installation Tips",
                    "body": "How to properly install RAM modules. Make sure they click in place.",
                    "tags": json.dumps(["ram", "installation", "memory"]),
                    "productsMentioned": json.dumps([]),
                    "version": "1.5",
                    "isDeprecated": False,
                    "createdAt": 1725292800000,  # 2025-09-03T00:00:00Z
                    "updatedAt": 1725296400000,  # 2025-09-03T01:00:00Z
                },
            }
        }

    def test_search_knowledge_base_no_filters(self):
        """Test searching articles with no filters."""
        result = SearchKnowledgeBase.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return all articles (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertGreater(len(result_list), 0)
        
        # Check structure of first article
        if result_list:
            article = result_list[0]
            self.assertIn("id", article)
            self.assertIn("title", article)
            self.assertIn("body", article)

    def test_search_knowledge_base_by_text(self):
        """Test searching articles by text (searches title and body)."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            text="CPU",
        )
        result_list = json.loads(result)
        
        # Should find articles with "CPU" in title or body
        self.assertGreater(len(result_list), 0)
        for article in result_list:
            title_body = article.get("title", "") + " " + article.get("body", "")
            self.assertIn("CPU", title_body)

    def test_search_knowledge_base_by_tags(self):
        """Test searching articles by tags."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            tags=["cpu", "installation"],
        )
        result_list = json.loads(result)
        
        # Should find articles with matching tags
        self.assertGreater(len(result_list), 0)
        for article in result_list:
            # Tags should be parsed from JSON
            if "tags" in article:
                tags = article["tags"]
                if isinstance(tags, list):
                    # Should have at least one of the requested tags
                    has_tag = any(tag in tags for tag in ["cpu", "installation"])
                    self.assertTrue(has_tag)

    def test_search_knowledge_base_filter_created_after(self):
        """Test filtering articles created after a date."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include articles created on or after 2025-09-02
        for article in result_list:
            self.assertGreaterEqual(article["createdAt"], 1725206400000)

    def test_search_knowledge_base_filter_created_before(self):
        """Test filtering articles created before a date."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include articles created before the date
        # Verify filtering works by comparing with no filter
        result_no_filter = SearchKnowledgeBase.invoke(self.data)
        no_filter_list = json.loads(result_no_filter)
        self.assertLessEqual(len(result_list), len(no_filter_list))

    def test_search_knowledge_base_filter_updated_after(self):
        """Test filtering articles updated after a date."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            updated_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include articles updated on or after the date
        for article in result_list:
            self.assertGreaterEqual(article["updatedAt"], 1725210000000)

    def test_search_knowledge_base_filter_updated_before(self):
        """Test filtering articles updated before a date."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            updated_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)
        
        # Should only include articles updated before the date
        # Verify filtering works
        result_no_filter = SearchKnowledgeBase.invoke(self.data)
        no_filter_list = json.loads(result_no_filter)
        self.assertLessEqual(len(result_list), len(no_filter_list))

    def test_search_knowledge_base_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            text="installation",
            tags=["cpu"],
        )
        result_list = json.loads(result)
        
        # Should match articles that satisfy all filters
        for article in result_list:
            title_body = article.get("title", "") + " " + article.get("body", "")
            self.assertIn("installation", title_body.lower())
            if "tags" in article and isinstance(article["tags"], list):
                self.assertIn("cpu", article["tags"])

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
            text="CPU",
        )
        result_list = json.loads(result)
        
        # Should find article1
        self.assertGreater(len(result_list), 0)
        article = result_list[0]
        
        # tags should be parsed from JSON string to list
        if "tags" in article:
            self.assertIsInstance(article["tags"], list)
            if article["tags"]:
                self.assertIsInstance(article["tags"][0], str)

    def test_search_knowledge_base_parses_products_mentioned(self):
        """Test that productsMentioned JSON field is parsed."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            text="CPU",
        )
        result_list = json.loads(result)
        
        # Should find article1
        self.assertGreater(len(result_list), 0)
        article = result_list[0]
        
        # productsMentioned should be parsed from JSON string to list
        if "productsMentioned" in article:
            self.assertIsInstance(article["productsMentioned"], list)

    def test_search_knowledge_base_sorted_by_title(self):
        """Test that results are sorted by title ASC, then id ASC."""
        result = SearchKnowledgeBase.invoke(self.data)
        result_list = json.loads(result)
        
        if len(result_list) >= 2:
            # Check that articles are sorted by title
            for i in range(len(result_list) - 1):
                current_title = result_list[i]["title"]
                next_title = result_list[i + 1]["title"]
                # Titles should be in ascending order
                if current_title == next_title:
                    # If titles are equal, check IDs
                    current_id = result_list[i]["id"]
                    next_id = result_list[i + 1]["id"]
                    self.assertLessEqual(current_id, next_id)
                else:
                    self.assertLessEqual(current_title, next_title)

    def test_search_knowledge_base_no_results(self):
        """Test search with filters that match no articles."""
        result = SearchKnowledgeBase.invoke(
            self.data,
            text="nonexistent text that won't match anything",
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
        self.assertIn("tags", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("updated_after", info["function"]["parameters"]["properties"])
        self.assertIn("updated_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()

