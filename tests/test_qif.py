"""
Created on 2024-09-30

@author: wf
"""

from nomina.qif import SplitCategory, SimpleQifParser
from tests.basetest import Basetest
from tests.example_testcases import NominaExample


class Test_QifParser(Basetest):
    """
    test QifParser
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples = NominaExample.get_examples()

    def test_split_categories(self):
        """
        test Quicken Interchange Format (QIF) split_categories
        """
        test_cases = [
            ("[Savings]", None, "Savings", None),
            ("Checking", "Checking", None, None),  # split_category
            ("Expenses:Groceries", "Expenses:Groceries", None, None),
            (
                "Kursgewinne:Realisierte Gewinne|[PrivatGiro]",
                "Kursgewinne:Realisierte Gewinne",
                "PrivatGiro",
                None,
            ),
            (
                "[Mehrwertsteuer]/_VATCode_N1_I",
                None,
                "Mehrwertsteuer",
                "_VATCode_N1_I",
            ),
            (
                "/_VATCode_B_I",
                None,
                None,
                "_VATCode_B_I",
            ),
        ]
        debug = self.debug
        debug = True
        for qif_markup, ex_category, ex_account, ex_class in test_cases:
            split_category = SplitCategory(qif_markup)
            if debug:
                print(f"{qif_markup}:{split_category}")
            self.assertEqual(ex_category, split_category.category, qif_markup)
            self.assertEqual(ex_account, split_category.account, qif_markup)

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

    def test_account_types(self):
        """
        test account type handling
        """
        test_cases = [
            ("!Account\nNMy Cash\nTCash\n^", "Cash"),
            ("!Account\nNMy Bank\nTBank\n^", "Bank"),
            ("!Account\nNMy CCard\nTCCard\n^", "CCard"),
            ("!Account\nNMy Invst\nTInvst\n^", "Invst"),
            ("!Account\nNMy Asset\nTOth A\n^", "Oth A"),
            ("!Account\nNMy Liability\nTOth L\n^", "Oth L"),
            ("!Account\nNMy Invoice\nTInvoice\n^", "Invoice")
        ]
        for qif_text, expected_type in test_cases:
            with self.subTest(f"Testing account type {expected_type}"):
                parser = SimpleQifParser()
                parser.parse(qif_text.splitlines())
                # Get first (and only) account
                account = next(iter(parser.accounts.values()))
                self.assertEqual(expected_type, account.account_type)