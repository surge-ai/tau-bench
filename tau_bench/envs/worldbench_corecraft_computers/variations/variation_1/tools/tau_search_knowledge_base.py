import json
from typing import Any, Dict, List, Optional

from tau_bench.envs.tool import Tool

from .data_utils import (
    iter_entities,
    parse_iso_datetime,
    parse_entity_json_fields,
    parse_json_field,
    get_created_at,
    get_updated_at,
    matches_text_search,
    apply_limit,
)


class SearchKnowledgeBase(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        text: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        updated_after: Optional[str] = None,
        updated_before: Optional[str] = None,
        limit: Optional[float] = None,
        **kwargs,
    ) -> str:
        results: List[Dict[str, Any]] = []

        # Parse date filters
        created_after_dt = parse_iso_datetime(created_after) if created_after else None
        created_before_dt = parse_iso_datetime(created_before) if created_before else None
        updated_after_dt = parse_iso_datetime(updated_after) if updated_after else None
        updated_before_dt = parse_iso_datetime(updated_before) if updated_before else None

        for row in iter_entities(data, "knowledgeBaseArticle"):
            # Text search in title and body
            if text and not matches_text_search(row, ["title", "body"], text):
                continue
            # Category filtering (exact match)
            if category and row.get("category") != category:
                continue
            # Single tag filtering
            if tag:
                row_tags = row.get("tags")
                if isinstance(row_tags, str):
                    row_tags = parse_json_field(row_tags)
                if not isinstance(row_tags, list) or tag not in row_tags:
                    continue
            # Tags filtering (array - all must be present)
            if tags:
                row_tags = row.get("tags")
                if isinstance(row_tags, str):
                    row_tags = parse_json_field(row_tags)
                if not isinstance(row_tags, list):
                    continue
                # All specified tags must be present
                if not all(t in row_tags for t in tags):
                    continue
            # Date filtering - createdAt
            created_at = get_created_at(row)
            if created_at is not None:
                if created_after_dt and created_at < created_after_dt:
                    continue
                if created_before_dt and created_at >= created_before_dt:
                    continue
            # Date filtering - updatedAt
            updated_at = get_updated_at(row)
            if updated_at is not None:
                if updated_after_dt and updated_at < updated_after_dt:
                    continue
                if updated_before_dt and updated_at >= updated_before_dt:
                    continue

            # Parse JSON fields
            result_row = parse_entity_json_fields(row, ["tags", "productsMentioned"])
            results.append(result_row)

        # Sort by title ASC, then by id ASC
        results.sort(key=lambda a: (a.get("title", ""), a.get("id", "")))

        # Apply limit
        results = apply_limit(results, limit)

        return json.dumps(results, default=str)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "searchKnowledgeBase",
                "description": "Search for knowledge base articles with various filters. Returns an array of article records matching the criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to search in title and body"
                        },
                        "category": {
                            "type": "string",
                            "description": "Category to filter by (exact match)"
                        },
                        "tag": {
                            "type": "string",
                            "description": "Single tag to filter by"
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Tags to filter by (all must be present)"
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter articles created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "created_before": {
                            "type": "string",
                            "description": "Filter articles created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "updated_after": {
                            "type": "string",
                            "description": "Filter articles updated after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "updated_before": {
                            "type": "string",
                            "description": "Filter articles updated before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default 50, max 200)"
                        }
                    },
                    "required": []
                }
            }
        }
