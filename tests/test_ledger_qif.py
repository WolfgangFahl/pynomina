"""
Created on 2024-10-06

@author: wf
"""
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
        # for name, example in self.examples.items():
        #    with self.subTest(f"Testing {name}"):
        example = self.examples[name]
        sqp = example.get_parsed_qif()
        if self.debug:
            sqp.show_summary()
        converter = QifToLedgerConverter(sqp)
        book = converter.convert_to_ledger_book()
        book.url = example.url
        book.owner = example.owner
        book.save_to_yaml_file(f"/tmp/{name}.yaml")
        stats = book.get_stats()
        example.check_stats(stats)
        pass
