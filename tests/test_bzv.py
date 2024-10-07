"""
Created on 2024-10-07

@author: wf
"""

from pathlib import Path

from nomina.bzv import Book
from nomina.stats import Stats
from tests.basetest import Basetest
from tests.example_testcases import NominaExample


class Test_BZV(Basetest):
    """
    test Banking ZV
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_read_bzv(self):
        """
        test reading Banking ZV files
        """
        bzv_example = self.examples_path + "/expenses2024.json"
        account_json_dict = {"expenses": bzv_example}
        book = Book(account_json_dict, name="expenses2024", owner="John doe")
        stats = book.get_stats()
        if self.debug:
            stats.show()
        example = NominaExample(
            name="expenses2024",
            owner="John Doe",
            url=None,
            example_path=Path(self.examples_path),
            expected_stats=Stats(accounts=2, transactions=2),
        )
        example.check_stats(stats)
