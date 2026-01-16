import json
from datetime import datetime
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class GetTimeDiff(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        start_date: str,
        end_date: str,
    ) -> str:
        """
        Calculate the time difference between two dates.

        Args:
            data: The data dictionary (unused but required by Tool interface)
            start_date: Start date in ISO format (e.g., "2025-01-15T12:00:00Z")
            end_date: End date in ISO format (e.g., "2025-03-20T12:00:00Z")

        Returns:
            JSON string with time difference in months and days
        """
        try:
            # Parse dates - handle both with and without timezone
            # Remove 'Z' if present and parse
            start_str = start_date.replace('Z', '+00:00') if start_date.endswith('Z') else start_date
            end_str = end_date.replace('Z', '+00:00') if end_date.endswith('Z') else end_date

            # Try parsing with timezone info first
            try:
                start_dt = datetime.fromisoformat(start_str)
                end_dt = datetime.fromisoformat(end_str)
            except ValueError:
                # If that fails, try without timezone
                start_dt = datetime.fromisoformat(start_date.rstrip('Z'))
                end_dt = datetime.fromisoformat(end_date.rstrip('Z'))

        except (ValueError, AttributeError) as e:
            return json.loads(json.dumps({
                "error": f"Invalid date format. Expected ISO format (e.g., '2025-01-15T12:00:00Z'). Error: {str(e)}"
            }))

        # Calculate difference
        delta = end_dt - start_dt
        if delta.days < 0:
            return json.loads(json.dumps({
                "error": "start_date is after end_date"
            }))
        # Get total days (can be negative if end is before start)
        total_days = delta.days + (delta.seconds / 86400)

        # Calculate months (approximate: 30.44 days per month on average)
        # Using 365.25 / 12 = 30.4375 for more accuracy
        days_per_month = 365.25 / 12
        total_months = total_days / days_per_month

        return json.loads(json.dumps({
            "start_date": start_date,
            "end_date": end_date,
            "difference": {
                "days": round(total_days, 2),
                "months": round(total_months, 2),
            },
            "is_negative": total_days < 0,
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_time_diff",
                "description": "Calculate the time difference between two dates, returning the result in both days and months as decimal values. For example, a difference might be 54.5 days or 1.79 months. Supports ISO 8601 date formats.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in ISO 8601 format (e.g., '2025-01-15T12:00:00Z' or '2025-01-15').",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in ISO 8601 format (e.g., '2025-03-20T12:00:00Z' or '2025-03-20'). If end_date is before start_date, the result will be negative.",
                        },
                    },
                    "required": ["start_date", "end_date"],
                },
            },
        }
