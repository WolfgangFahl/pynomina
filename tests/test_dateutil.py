"""
Created on 2024-10-05

@author: wf
"""

from nomina.date_utils import DateUtils
from tests.basetest import Basetest


class Test_Dateutils(Basetest):
    """
    test dateutils
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_split_date_range(self):
        """
        Test splitting a date range into sub-ranges.
        """
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        num_ranges = 4

        date_ranges = DateUtils.split_date_range(start_date, end_date, num_ranges)

        expected_ranges = [
            ("2023-01-01", "2023-04-01"),
            ("2023-04-02", "2023-07-01"),
            ("2023-07-02", "2023-09-30"),
            ("2023-10-01", "2023-12-31"),
        ]
        self.assertEqual(
            date_ranges,
            expected_ranges,
            "Date ranges do not match the expected output.",
        )
