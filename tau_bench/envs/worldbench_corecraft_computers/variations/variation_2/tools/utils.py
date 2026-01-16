"""Utility functions for variation_2 tools."""

from typing import Any, Dict, Optional, Set


# Valid data keys that exist in the data dictionary
VALID_DATA_KEYS: Set[str] = {
    "customer",
    "order",
    "support_ticket",
    "payment",
    "shipment",
    "product",
    "build",
    "employee",
    "refund",
    "escalation",
    "resolution",
    "knowledge_base_article",
    "slack_channel",
    "slack_message",
}

# Aliases for convenience (e.g., "ticket" -> "support_ticket")
ENTITY_TYPE_ALIASES: Dict[str, str] = {
    "ticket": "support_ticket",
}

# Valid entity type values for enum (includes both data keys and aliases)
VALID_ENTITY_TYPES: list = sorted(list(VALID_DATA_KEYS) + list(ENTITY_TYPE_ALIASES.keys()))


def get_entity_data_key(entity_type: str) -> Optional[str]:
    """
    Get the data key for an entity type, handling aliases.

    Args:
        entity_type: Entity type name (e.g., "order", "ticket", "support_ticket")

    Returns:
        Data key to use in data dict, or None if unknown entity type

    Examples:
        >>> get_entity_data_key("order")
        'order'
        >>> get_entity_data_key("ticket")
        'support_ticket'
        >>> get_entity_data_key("CUSTOMER")
        'customer'
    """
    entity_type_lower = entity_type.lower()

    # Check if it's an alias
    if entity_type_lower in ENTITY_TYPE_ALIASES:
        return ENTITY_TYPE_ALIASES[entity_type_lower]

    # Check if it's a valid data key
    if entity_type_lower in VALID_DATA_KEYS:
        return entity_type_lower

    return None


def get_entity_table(data: Dict[str, Any], entity_type: str) -> Optional[Dict[str, Any]]:
    """
    Get entity table from data, handling entity type aliases.

    Args:
        data: Data dict containing entity tables
        entity_type: Entity type name

    Returns:
        Entity table dict, or None if not found or invalid type

    Example:
        >>> data = {"order": {...}, "support_ticket": {...}}
        >>> get_entity_table(data, "ticket")  # Using alias
        {...}  # Returns support_ticket table
    """
    data_key = get_entity_data_key(entity_type)
    if not data_key:
        return None

    entity_table = data.get(data_key, {})
    if not isinstance(entity_table, dict):
        return None

    return entity_table


def validate_enum_value(value: str, allowed_values: list, param_name: str) -> Optional[str]:
    """
    Validate that a value is in the allowed enum values.

    Args:
        value: The value to validate
        allowed_values: List of allowed values
        param_name: Name of the parameter (for error messages)

    Returns:
        None if valid, error message string if invalid

    Example:
        >>> error = validate_enum_value("open", ["open", "closed"], "status")
        >>> error is None
        True
        >>> error = validate_enum_value("invalid", ["open", "closed"], "status")
        >>> "invalid" in error
        True
    """
    if value not in allowed_values:
        return f"Invalid {param_name}: '{value}'. Allowed values: {', '.join(allowed_values)}"
    return None


def format_invalid_entity_type_error(entity_type: str) -> Dict[str, Any]:
    """Format a standard invalid entity type error message."""
    return {
        "error": f"Unknown entity type: '{entity_type}'",
        "provided_type": entity_type,
        "valid_types": sorted(VALID_DATA_KEYS),
        "aliases": dict(ENTITY_TYPE_ALIASES),
    }


# Standard field schemas for each entity type
# These define the valid fields that can be updated for each entity
# Extracted from actual data using extract_actual_schema.py
ENTITY_FIELD_SCHEMAS: Dict[str, Set[str]] = {
    "build": {
        "componentIds",
        "createdAt",
        "customerId",
        "name",
        "ownerType",
        "updatedAt",
    },
    "bundle": {
        "componentIds",
        "discount",
        "name",
    },
    "compatibility_rule": {
        "appliesToCategories",
        "logic",
        "name",
        "severity",
    },
    "customer": {
        "addresses",
        "createdAt",
        "dateOfBirth",
        "email",
        "id",
        "loyaltyTier",
        "name",
        "phone",
        "type",
    },
    "employee": {
        "createdAt",
        "department",
        "email",
        "managerId",
        "name",
        "permissions",
        "supportRole",
        "title",
    },
    "escalation": {
        "createdAt",
        "destination",
        "escalationType",
        "notes",
        "resolvedAt",
        "ticketId",
    },
    "knowledge_base_article": {
        "body",
        "createdAt",
        "isDeprecated",
        "productsMentioned",
        "tags",
        "title",
        "updatedAt",
        "version",
    },
    "linkedin_profile": {
        "about",
        "applicantId",
        "certifications",
        "city",
        "country",
        "createdAt",
        "education",
        "fullName",
        "headline",
        "jobBoardProfileId",
        "languages",
        "lastUpdatedOnLinkedin",
        "profileUrl",
        "projects",
        "schemaVersion",
        "skills",
        "state",
        "updatedAt",
        "volunteerExperience",
        "workExperience",
    },
    "order": {
        "buildId",
        "createdAt",
        "customerId",
        "failureReason",
        "id",
        "lineItems",
        "shipping",
        "status",
        "total",
        "type",
        "updatedAt",
    },
    "payment": {
        "amount",
        "createdAt",
        "customerId",
        "failureReason",
        "id",
        "method",
        "orderId",
        "processedAt",
        "status",
        "transactionId",
        "type",
    },
    "product": {
        "brand",
        "category",
        "inventory",
        "name",
        "price",
        "sku",
        "specs",
        "warrantyMonths",
    },
    "refund": {
        "amount",
        "createdAt",
        "lines",
        "paymentId",
        "processedAt",
        "reason",
        "status",
        "ticketId",
    },
    "resolution": {
        "createdAt",
        "details",
        "linkedRefundId",
        "outcome",
        "resolvedById",
        "ticketId",
    },
    "shipment": {
        "carrier",
        "createdAt",
        "eta",
        "events",
        "orderId",
        "status",
        "trackingNumber",
    },
    "slack_channel": {
        "members",
        "name",
        "purpose",
    },
    "slack_message": {
        "authorId",
        "channelId",
        "reactions",
        "text",
        "ticketId",
        "timestamp",
    },
    "support_ticket": {
        "assignedEmployeeId",
        "body",
        "buildId",
        "channel",
        "closureReason",
        "createdAt",
        "customerId",
        "description",
        "id",
        "orderId",
        "priority",
        "resolutionId",
        "status",
        "subject",
        "ticketType",
        "updatedAt",
    },
}


def get_valid_fields_for_entity_type(entity_type: str) -> Optional[Set[str]]:
    """
    Get the set of valid field names for an entity type.

    Args:
        entity_type: Entity type name (can use aliases like "ticket")

    Returns:
        Set of valid field names, or None if entity type is unknown

    Example:
        >>> fields = get_valid_fields_for_entity_type("order")
        >>> "status" in fields
        True
        >>> "invalidField" in fields
        False
    """
    # Resolve aliases
    data_key = get_entity_data_key(entity_type)
    if not data_key:
        return None

    return ENTITY_FIELD_SCHEMAS.get(data_key)


def get_now_iso_from_data(data: Dict[str, Any]) -> str:
    """
    Get deterministic timestamp from data or use fallback.

    Checks for timestamp in data under various common keys (__now, now, current_time, currentTime).
    Returns fallback timestamp if not found.

    Args:
        data: Data dict that may contain a timestamp

    Returns:
        ISO format timestamp string

    Example:
        >>> data = {"__now": "2024-01-15T10:30:00Z"}
        >>> get_now_iso_from_data(data)
        '2024-01-15T10:30:00Z'
        >>> get_now_iso_from_data({})
        '1970-01-01T00:00:00Z'
    """
    for k in ("__now", "now", "current_time", "currentTime"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return "1970-01-01T00:00:00Z"
