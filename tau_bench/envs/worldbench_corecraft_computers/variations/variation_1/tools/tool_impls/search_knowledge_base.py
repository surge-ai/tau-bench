import json
from typing import Annotated, List, Optional

from models import KnowledgeBaseArticle
from pydantic import Field
from utils import get_db_conn, validate_date_format, parse_datetime_to_timestamp


def searchKnowledgeBase(
    text: Annotated[Optional[str], Field(description="Text to search in title and body")] = None,
    tags: Annotated[Optional[List[str]], Field(description="Tags to filter by")] = None,
    created_after: Annotated[
        Optional[str],
        Field(description="Filter articles created after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")")
    ] = None,
    created_before: Annotated[
        Optional[str],
        Field(description="Filter articles created before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")")
    ] = None,
    updated_after: Annotated[
        Optional[str],
        Field(description="Filter articles updated after this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")")
    ] = None,
    updated_before: Annotated[
        Optional[str],
        Field(description="Filter articles updated before this date (ISO 8601 format with UTC timezone, e.g., \"2025-08-27T00:00:00Z\")")
    ] = None,
    limit: Annotated[
        Optional[float],
        Field(description="Maximum number of results (default 50, max 200)"),
    ] = None,
) -> List[KnowledgeBaseArticle]:
    """Search for knowledge base articles"""
    # Validate date formats
    if created_after:
        created_after = validate_date_format(created_after, "created_after")
    if created_before:
        created_before = validate_date_format(created_before, "created_before")
    if updated_after:
        updated_after = validate_date_format(updated_after, "updated_after")
    if updated_before:
        updated_before = validate_date_format(updated_before, "updated_before")
    
    limit = int(limit) if limit else 50
    limit = min(limit, 200)

    conditions = []
    params = []

    if text:
        conditions.append("(title LIKE ? OR body LIKE ?)")
        params.extend([f"%{text}%", f"%{text}%"])

    if tags:
        for tag in tags:
            conditions.append("tags LIKE ?")
            params.append(f'%"{tag}"%')

    if created_after:
        conditions.append("createdAt >= ?")
        params.append(parse_datetime_to_timestamp(created_after))

    if created_before:
        conditions.append("createdAt < ?")
        params.append(parse_datetime_to_timestamp(created_before))

    if updated_after:
        conditions.append("updatedAt >= ?")
        params.append(parse_datetime_to_timestamp(updated_after))

    if updated_before:
        conditions.append("updatedAt < ?")
        params.append(parse_datetime_to_timestamp(updated_before))

    params.append(limit)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM KnowledgeBaseArticle {where_clause} ORDER BY title ASC, id ASC LIMIT ?"

    conn = get_db_conn()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)

            # Parse JSON fields
            for field in ["tags", "productsMentioned"]:
                if field in row_dict and isinstance(row_dict[field], str):
                    try:
                        row_dict[field] = json.loads(row_dict[field])
                    except (json.JSONDecodeError, TypeError):
                        pass

            results.append(KnowledgeBaseArticle(**row_dict))

        return results
    finally:
        conn.close()
