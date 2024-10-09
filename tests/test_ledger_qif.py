"""
Created on 2024-10-06

@author: wf
"""

from copy import deepcopy

from nomina.qif_ledger import QifToLedgerConverter
from tests.basetest import Basetest
from tests.example_testcases import NominaExample


class Test_LedgerQif(Basetest):
    """
    test QIF handling
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples = NominaExample.get_examples(do_log=self.debug)

    def test_qif2ledger(self):
        """
        test the expenses example
        """
        name = "expenses"
        example = self.examples[name]
        qif_example = str(example.example_path) + "/expenses.qif"
        converter = QifToLedgerConverter()
        converter.load(qif_example)
        book = converter.convert_to_target()
        book.url = example.url
        book.owner = example.owner
        book.save_to_yaml_file(f"/tmp/{name}.yaml")
        stats = book.get_stats()
        if self.debug:
            stats.show()
        expected_stats = deepcopy(example.expected_stats)
        expected_stats.accounts += 2
        expected_stats.currencies["EUR"] += 5
        example.check_stats(stats, expected_stats=expected_stats)
        pass
