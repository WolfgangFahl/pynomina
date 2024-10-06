"""
Created on 2024-10-06

@author: wf
"""

from nomina.gnc_ledger import GnuCashToLedgerConverter, LedgerToGnuCashConverter
from tests.basetest import Basetest
from tests.example_testcases import NominaExample


class Test_LedgerGnuCash(Basetest):
    """
    test GnuCash handling
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples = NominaExample.get_examples()

    def test_ledger2gnucash(self):
        """
        test converting ledger format to GnuCash
        """
        for name, example in self.examples.items():
            with self.subTest(f"Testing {name}"):
                if self.debug:
                    print(f"loading ledger book {name} from yaml")
                ledger_book = example.get_ledger_book()
                if self.debug:
                    print(f"converting ledger book {name} to GnuCash")
                l2g = LedgerToGnuCashConverter(ledger_book)
                gncv2 = l2g.convert()
                if self.debug:
                    print(f"writing GnuCash xmlfile for {name} to /tmp ")
                example.write_gnucash(gncv2, "/tmp", "l2g")
                pass

    def test_gnucash2ledger(self):
        """
        test converting gnu cash to ledger format
        """
        for name, example in self.examples.items():
            with self.subTest(f"Testing {name}"):
                if self.debug:
                    print(f"loading {name} GnuCash from xml")
                gncv2 = example.get_parsed_gnucash()
                g2l = GnuCashToLedgerConverter(gncv2)
                if self.debug:
                    print(f"converting  {name} GnuCash to ledger book")
                ledger_book = g2l.convert(owner=example.owner, url=example.url)
                if self.debug:
                    print(f"writing  {name} ledger book to yaml in /tmp")
                ledger_book.save_to_yaml_file(f"/tmp/{name}_g2l.yaml")
                pass
