import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_get_time_diff import GetTimeDiff


class TestGetTimeDiff(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        self.data: Dict[str, Any] = {
            "__now": "2025-01-15T12:00:00Z",
        }

    def test_time_diff_days_simple(self):
        """Test simple time difference in days."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-01-11T00:00:00Z",
        )

        self.assertIn("difference", result)
        self.assertEqual(result["difference"]["days"], 10.0)
        self.assertFalse(result["is_negative"])

    def test_time_diff_months_simple(self):
        """Test time difference in months (approximately 1 month)."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-02-01T00:00:00Z",
        )

        self.assertIn("difference", result)
        # 31 days / 30.4375 days per month = ~1.02 months
        self.assertAlmostEqual(result["difference"]["months"], 1.02, places=1)
        self.assertEqual(result["difference"]["days"], 31.0)

    def test_time_diff_two_months(self):
        """Test time difference of approximately 2 months."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-03-01T00:00:00Z",
        )

        self.assertIn("difference", result)
        # 59 days (Jan + Feb in non-leap year)
        self.assertEqual(result["difference"]["days"], 59.0)
        # 59 / 30.4375 = ~1.94 months
        self.assertAlmostEqual(result["difference"]["months"], 1.94, places=1)

    def test_time_diff_half_day(self):
        """Test time difference with fractional days."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-01-01T12:00:00Z",
        )

        self.assertIn("difference", result)
        self.assertEqual(result["difference"]["days"], 0.5)
        # 0.5 days / 30.4375 days per month = ~0.016 months
        self.assertAlmostEqual(result["difference"]["months"], 0.02, places=2)

    def test_time_diff_negative(self):
        """Test negative time difference (end before start)."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-15T00:00:00Z",
            end_date="2025-01-10T00:00:00Z",
        )

        self.assertIn("difference", result)
        self.assertEqual(result["difference"]["days"], -5.0)
        self.assertTrue(result["is_negative"])

    def test_time_diff_same_date(self):
        """Test time difference when dates are the same."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-15T12:00:00Z",
            end_date="2025-01-15T12:00:00Z",
        )

        self.assertIn("difference", result)
        self.assertEqual(result["difference"]["days"], 0.0)
        self.assertEqual(result["difference"]["months"], 0.0)
        self.assertFalse(result["is_negative"])

    def test_time_diff_one_year(self):
        """Test time difference of one year."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2024-01-01T00:00:00Z",
            end_date="2025-01-01T00:00:00Z",
        )

        self.assertIn("difference", result)
        # 366 days (2024 is a leap year)
        self.assertEqual(result["difference"]["days"], 366.0)
        # 366 / 30.4375 = ~12.03 months
        self.assertAlmostEqual(result["difference"]["months"], 12.0, places=0)

    def test_time_diff_date_only_format(self):
        """Test with date-only format (no time component)."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01",
            end_date="2025-01-31",
        )

        self.assertIn("difference", result)
        self.assertEqual(result["difference"]["days"], 30.0)

    def test_time_diff_with_hours_minutes_seconds(self):
        """Test with precise time including hours, minutes, seconds."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01T10:30:45Z",
            end_date="2025-01-02T14:45:30Z",
        )

        self.assertIn("difference", result)
        # Should be slightly more than 1 day (about 1.18 days)
        self.assertGreater(result["difference"]["days"], 1.0)
        self.assertLess(result["difference"]["days"], 1.2)

    def test_time_diff_leap_year(self):
        """Test time difference across a leap year."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2024-02-28T00:00:00Z",
            end_date="2024-03-01T00:00:00Z",
        )

        self.assertIn("difference", result)
        # 2024 is a leap year, so Feb has 29 days
        self.assertEqual(result["difference"]["days"], 2.0)

    def test_time_diff_long_period(self):
        """Test time difference over a long period."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2020-01-01T00:00:00Z",
            end_date="2025-01-01T00:00:00Z",
        )

        self.assertIn("difference", result)
        # 5 years = approximately 1826 or 1827 days (including leap years)
        self.assertGreater(result["difference"]["days"], 1800)
        self.assertLess(result["difference"]["days"], 1900)
        # Should be approximately 60 months
        self.assertGreater(result["difference"]["months"], 59)
        self.assertLess(result["difference"]["months"], 61)

    def test_time_diff_invalid_start_date(self):
        """Test with invalid start date format."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="invalid-date",
            end_date="2025-01-15T00:00:00Z",
        )

        self.assertIn("error", result)
        self.assertIn("Invalid date format", result["error"])

    def test_time_diff_invalid_end_date(self):
        """Test with invalid end date format."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-15T00:00:00Z",
            end_date="not-a-date",
        )

        self.assertIn("error", result)
        self.assertIn("Invalid date format", result["error"])

    def test_time_diff_both_dates_invalid(self):
        """Test with both dates invalid."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="invalid",
            end_date="also-invalid",
        )

        self.assertIn("error", result)
        self.assertIn("Invalid date format", result["error"])

    def test_time_diff_partial_month(self):
        """Test time difference that's a partial month."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-01-16T00:00:00Z",
        )

        self.assertIn("difference", result)
        self.assertEqual(result["difference"]["days"], 15.0)
        # 15 days / 30.4375 days per month = ~0.49 months
        self.assertAlmostEqual(result["difference"]["months"], 0.49, places=1)

    def test_time_diff_precise_calculation(self):
        """Test that calculation is precise with seconds."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-01-01T01:00:00Z",
        )

        self.assertIn("difference", result)
        # 1 hour = 1/24 of a day
        expected_days = 1.0 / 24.0
        self.assertAlmostEqual(result["difference"]["days"], expected_days, places=2)

    def test_time_diff_result_structure(self):
        """Test that result has correct structure."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-01-15T00:00:00Z",
        )

        self.assertIn("start_date", result)
        self.assertIn("end_date", result)
        self.assertIn("difference", result)
        self.assertIn("is_negative", result)
        self.assertIn("days", result["difference"])
        self.assertIn("months", result["difference"])

        # Check types
        self.assertIsInstance(result["difference"]["days"], (int, float))
        self.assertIsInstance(result["difference"]["months"], (int, float))
        self.assertIsInstance(result["is_negative"], bool)

    def test_time_diff_without_z_suffix(self):
        """Test with ISO format without Z suffix."""
        result = GetTimeDiff.invoke(
            self.data,
            start_date="2025-01-01T00:00:00",
            end_date="2025-01-11T00:00:00",
        )

        self.assertIn("difference", result)
        self.assertEqual(result["difference"]["days"], 10.0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetTimeDiff.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "get_time_diff")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])

        params = info["function"]["parameters"]
        self.assertIn("start_date", params["properties"])
        self.assertIn("end_date", params["properties"])

        # Check required fields
        required = params["required"]
        self.assertIn("start_date", required)
        self.assertIn("end_date", required)


if __name__ == "__main__":
    unittest.main()
