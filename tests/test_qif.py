"""
Created on 2024-09-30

@author: wf
"""

from nomina.qif import SplitTarget
from tests.basetest import Basetest
from tests.example_testcases import NominaExample


class Test_QifParser(Basetest):
    """
    test QifParser
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples = NominaExample.get_examples()

    def test_split_targets(self):
        """
        test split targets
        """

        test_targets = [
            "[Savings]",
            "Checking",
            "Expenses:Groceries",
            "Checking/Groceries",
            "Kursgewinne:Realisierte Gewinne|[PrivatGiro]",
        ]

        for test_target in test_targets:
            split_target = SplitTarget(test_target)
            if self.debug:
                print(f"{test_target}:{split_target}")

    def test_qif_examples(self):
        """
        test the qif example
        """
        for name, example in self.examples.items():
            if example.is_qif:
                with self.subTest(f"Testing {name}"):
                    sqp = example.get_parsed_qif()
                    if self.debug:
                        sqp.show_summary()
                    stats = sqp.get_stats()
                    self.assertEqual(
                        stats.transactions, example.expected_stats.transactions
                    )
                    self.assertEqual(
                        stats.start_date, example.expected_stats.start_date
                    )
                    self.assertEqual(stats.end_date, example.expected_stats.end_date)
