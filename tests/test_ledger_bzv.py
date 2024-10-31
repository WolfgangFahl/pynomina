"""
Created on 2024-10-08

@author: wf
"""

from pathlib import Path

from nomina.bzv import Book
from nomina.bzv_ledger import BankingZVToLedgerConverter
from nomina.stats import Stats
from tests.basetest import Basetest
from tests.example_testcases import NominaExample


class Test_Ledger_BankingZV(Basetest):
    """
    test Banking ZV Subsembly handling
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_banking_zv_to_ledger(self):
        """
        test converting Banking ZV format to ledger
        """
        bzv_example = self.examples_path + "/expenses2024_bzv.yaml"
        converter = BankingZVToLedgerConverter(debug=self.debug)
        banking_zv_book = converter.load(bzv_example)
        self.assertIsInstance(banking_zv_book, Book)
        ledger_book = converter.convert_to_target()
        stats = ledger_book.get_stats()
        if self.debug:
            stats.show()
        example = NominaExample(
            name="expenses_2024",
            owner="John Doe",
            url=None,
            example_path=Path(self.examples_path),
            do_log=True,
            expected_stats=Stats(
                accounts=7,
                transactions=3,
                start_date="2022-09-08",
                end_date="2024-10-06",
                currencies={
                    "EUR": 7,
                },
            ),
        )
        wrong = example.check_stats(stats)
        self.assertEqual(0, wrong)
