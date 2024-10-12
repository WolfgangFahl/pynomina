"""
Created on 2024-10-02

@author: wf
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple


class DateUtils:
    """
    date utilities
    """

    @staticmethod
    def iso_date(date: datetime) -> str:
        """
        Format a datetime object to a string in 'YYYY-MM-DD' format.

        Args:
            date (datetime): The date to format.

        Returns:
            str: The formatted date as a string.
        """
        return date.strftime("%Y-%m-%d")

    @classmethod
    def parse_date(
        cls, date_str: str, date_formats: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Parse the given date string using the provided formats.

        Args:
            date_str (str): The date string to parse.
            date_formats (List[str], optional): List of date formats to try.
                If None, uses a default list of formats.

        Returns:
            Optional[str]: The parsed date in ISO format (YYYY-MM-DD) or None if parsing fails.
        """
        if date_formats is None:
            date_formats = [
                "%m.%d.%y",
                "%d.%m.%y",
                "%m/%d/%y",
                "%d/%m/%y",
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y-%m-%d %H:%M:%S %z",  # Added to handle the GnuCash XML format
                "%m/%d/%y %H:%M:%S",  # Microsoft Money
            ]

        for date_format in date_formats:
            try:
                date_obj = datetime.strptime(date_str, date_format)
                return cls.iso_date(date_obj)
            except ValueError:
                continue

        return None

    @classmethod
    def split_date_range(
        cls, start_date: str, end_date: str, num_ranges: int
    ) -> List[Tuple[str, str]]:
        """
        Splits a date range into a predefined number of sub-ranges.

        Args:
            start_date (str): The start date in "YYYY-MM-DD" format.
            end_date (str): The end date in "YYYY-MM-DD" format.
            num_ranges (int): The number of ranges to split into.

        Returns:
            List[Tuple[str, str]]: A list of tuples representing the sub-ranges.
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        total_days = (end - start).days

        base_range_length = total_days // num_ranges
        extra_days = total_days % num_ranges

        ranges = []
        current_start = start
        for i in range(num_ranges):
            range_length = base_range_length + (1 if i < extra_days else 0)
            current_end = current_start + timedelta(days=range_length - 1)

            ranges.append((cls.iso_date(current_start), cls.iso_date(current_end)))
            current_start = current_end + timedelta(days=1)

        # Ensure the last range ends on the specified end date
        ranges[-1] = (ranges[-1][0], end_date)

        return ranges
