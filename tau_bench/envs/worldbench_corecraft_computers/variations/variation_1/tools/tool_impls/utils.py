import os
import sys

# Use pysqlite3-binary on Linux for guaranteed JSON1 extension support
# On macOS, the system sqlite3 includes JSON1 support (since SQLite 3.38.0)
if sys.platform == "linux":
    import pysqlite3.dbapi2 as sqlite3
else:
    import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def get_worldbench_base_dir() -> Path:
    """Get the worldbench base directory.

    Returns the WORLDBENCH_ROOT environment variable if set,
    otherwise derives it from the current file path.
    """
    worldbench_root = os.environ.get("WORLDBENCH_ROOT")
    if worldbench_root:
        return Path(worldbench_root)
    return Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def get_db_conn(read_only: bool = False) -> sqlite3.Connection:
    """Get a database connection."""
    # Use WORLDBENCH_DB_PATH from environment, or fall back to default
    db_path = os.environ.get("WORLDBENCH_DB_PATH")
    if not db_path:
        # Default fallback path
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "dev.db")

    if read_only:
        conn = sqlite3.connect(
            f"file:{db_path}?mode=ro&immutable=1", uri=True
        )
        conn.execute("PRAGMA query_only = ON")
    else:
        conn = sqlite3.connect(db_path)

    conn.row_factory = sqlite3.Row
    return conn


def validate_date_format(date_str: str, param_name: str) -> str:
    """Validate and normalize date string to UTC format with Z suffix.

    Accepts both UTC (with Z suffix) and timezone-aware ISO 8601 formats,
    converting timezone-aware strings to UTC.

    Args:
        date_str: Date string to validate
        param_name: Parameter name for error message

    Returns:
        Normalized date string in UTC format with Z suffix

    Raises:
        ValueError: If date format is invalid
    """
    try:
        # If already in UTC format with Z, return as-is
        if date_str.endswith("Z"):
            return date_str

        # Try to parse timezone-aware datetime and convert to UTC
        parsed_dt = datetime.fromisoformat(date_str)

        # If naive datetime, raise error asking for explicit timezone
        if parsed_dt.tzinfo is None:
            raise ValueError(
                f"{param_name} must include timezone information "
                f'(e.g., "2025-08-01T00:00:00Z" or "2025-08-01T00:00:00-07:00")'
            )

        # Convert to UTC and format with Z suffix
        utc_dt = parsed_dt.astimezone(timezone.utc)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    except (ValueError, AttributeError) as e:
        raise ValueError(
            f"{param_name} must be in ISO 8601 format with timezone "
            f'(e.g., "2025-08-01T00:00:00Z" or "2025-08-01T00:00:00-07:00"): {str(e)}'
        )


def parse_datetime_to_timestamp(date_str: str) -> int:
    """Parse an ISO 8601 date string to Unix timestamp in milliseconds.

    Args:
        date_str: ISO 8601 date string (e.g., "2025-08-01T00:00:00Z")

    Returns:
        Unix timestamp in milliseconds
    """
    dt_str = date_str.replace("Z", "+00:00")
    parsed_dt = datetime.fromisoformat(dt_str)

    # If the datetime is naive, assume UTC
    if parsed_dt.tzinfo is None:
        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)

    return int(parsed_dt.timestamp() * 1000)


def timestamp_to_iso_string(timestamp_ms: int) -> str:
    """Convert Unix timestamp in milliseconds to ISO 8601 string with timezone.

    Args:
        timestamp_ms: Unix timestamp in milliseconds

    Returns:
        ISO 8601 formatted string with timezone (e.g., "2025-09-14T23:47:00+00:00")
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    return dt.isoformat()
