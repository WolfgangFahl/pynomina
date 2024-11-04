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
        for name,accounts_diff,currencies_diff in [
             ("qifparser_test_file",0,0),
             ("expenses",2,5)
        ]:
            example = self.examples[name]
            qif_example = str(example.example_path) + "/"+name+".qif"
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
            expected_stats.accounts += accounts_diff
            expected_stats.currencies["EUR"] += currencies_diff
            example.check_stats(stats, expected_stats=expected_stats)
            pass
