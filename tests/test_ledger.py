"""
Created on 2024-10-05

@author: wf
"""

from nomina.ledger import Book
from tests.basetest import Basetest
from tests.example_testcases import NominaExample


class Test_Ledger(Basetest):
    """
    test Ledger
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples = NominaExample.get_examples()

    def test_ledger(self):
        """
        test ledger
        """
        for name, example in self.examples.items():
            with self.subTest(f"Testing {name}"):
                ledger_book = Book.load_from_yaml_file(
                    f"{example.example_path}/{name}.yaml"
                )
                stats = ledger_book.get_stats()
                if self.debug:
                    print(stats)
                example.check_stats(stats)
                pass
