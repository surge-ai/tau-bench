"""Shared utility functions for data-object-based tools.

These utilities provide common functionality for iterating over data tables,
parsing JSON fields, handling datetime comparisons, and other operations
needed by the tool implementations.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Sequence


def iter_entities(data: Dict[str, Any], table_name: str) -> Iterator[Dict[str, Any]]:
    """Iterate over entity records from a data table.

    Handles both dict-keyed and list formats:
    - Dict format: {"id1": {...}, "id2": {...}}
    - List format: [{...}, {...}]

    Args:
        data: The data dictionary to search
        table_name: Table name in snake_case (e.g., "customer", "order", "support_ticket")

    Yields:
        Individual entity records as dictionaries
    """
    table = data.get(table_name)
    if table is not None:
        if isinstance(table, dict):
            for row in table.values():
                if isinstance(row, dict):
                    yield row
        elif isinstance(table, list):
            for row in table:
                if isinstance(row, dict):
                    yield row


def get_entity_by_id(data: Dict[str, Any], table_name: str, entity_id: str) -> Optional[Dict[str, Any]]:
    """Get a single entity by ID from a data table.

    Args:
        data: The data dictionary to search
        table_name: Base table name (e.g., "customer", "order", "product")
        entity_id: The ID of the entity to retrieve

    Returns:
        The entity dictionary if found, None otherwise
    """
    for entity in iter_entities(data, table_name):
        if entity.get("id") == entity_id:
            return dict(entity)
    return None


def parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """Parse an ISO 8601 date string to a datetime object.

    Args:
        date_str: ISO 8601 date string (e.g., "2025-08-01T00:00:00Z")

    Returns:
        datetime object with timezone, or None if parsing fails
    """
    if not date_str:
        return None
    try:
        dt_str = date_str.replace("Z", "+00:00")
        parsed_dt = datetime.fromisoformat(dt_str)
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
        return parsed_dt
    except (ValueError, AttributeError):
        return None


def get_datetime_field(entity: Dict[str, Any], field: str) -> Optional[datetime]:
    """Get a datetime field from an entity.

    Handles both string (ISO 8601) and datetime values.

    Args:
        entity: The entity dictionary
        field: The field name to retrieve (e.g., "createdAt", "updatedAt", "processedAt")

    Returns:
        datetime object, or None if not present or invalid
    """
    value = entity.get(field)
    if value is None:
        return None
    if isinstance(value, str):
        return parse_iso_datetime(value)
    if isinstance(value, datetime):
        return value
    return None


def parse_json_field(value: Any) -> Any:
    """Parse a JSON string field if needed.

    Args:
        value: The value to potentially parse

    Returns:
        Parsed JSON object if value was a valid JSON string, otherwise original value
    """
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def parse_entity_json_fields(entity: Dict[str, Any], fields: Sequence[str]) -> Dict[str, Any]:
    """Parse specified JSON fields in an entity record.

    Args:
        entity: The entity dictionary
        fields: List of field names to parse

    Returns:
        Copy of entity with specified fields parsed from JSON
    """
    result = dict(entity)
    for field in fields:
        if field in result:
            result[field] = parse_json_field(result[field])
    return result


def matches_text_search(entity: Dict[str, Any], fields: Sequence[str], text: str) -> bool:
    """Check if any of the specified fields contain the search text (case insensitive).

    Args:
        entity: The entity dictionary
        fields: List of field names to search
        text: The text to search for

    Returns:
        True if any field contains the text (case insensitive)
    """
    text_lower = text.lower()
    for field in fields:
        value = entity.get(field, "")
        if isinstance(value, str) and text_lower in value.lower():
            return True
    return False


def matches_json_text_search(entity: Dict[str, Any], field: str, text: str) -> bool:
    """Check if a JSON field (as string or already parsed) contains the search text.

    Args:
        entity: The entity dictionary
        field: The field name to search
        text: The text to search for

    Returns:
        True if the field contains the text
    """
    value = entity.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        return text in value
    # Already parsed - convert to JSON string to search
    return text in json.dumps(value)


def apply_limit(results: List[Any], limit: Optional[float], max_limit: int = 200) -> List[Any]:
    """Apply a limit to results with a maximum cap.

    Args:
        results: The list of results
        limit: Optional limit value
        max_limit: Maximum allowed limit (default 200)

    Returns:
        Sliced results list
    """
    limit_val = int(limit) if limit else 50
    limit_val = min(limit_val, max_limit)
    return results[:limit_val]
