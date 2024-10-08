"""
Created on 2024-10-06

@author: wf
"""

import os

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
                l2g = LedgerToGnuCashConverter(debug=self.debug)
                output_path = os.path.join("/tmp", f"{name}_l2g_xml.gnucash")
                with open(output_path, "w") as gc_file:
                    l2g.convert(example.ledger_file, gc_file)
                if self.debug:
                    l2g.show_stats()

    def test_gnucash2ledger(self):
        """
        test converting gnu cash to ledger format
        """
        for name, example in self.examples.items():
            with self.subTest(f"Testing {name}"):
                g2l = GnuCashToLedgerConverter(debug=self.debug)
                output_path = os.path.join("/tmp", f"{name}_g2l.yaml")
                # owner=example.owner, url=example.url
                with open(output_path, "w") as ledger_file:
                    g2l.convert(example.gnu_cash_xml_file, ledger_file)
                if self.debug:
                    g2l.show_stats()
