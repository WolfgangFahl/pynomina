"""
Created on 2024-10-09

@author: wf
"""

from pathlib import Path

from nomina.msmoney_ledger import MicrosoftMoneyToLedgerConverter
from tests.basetest import Basetest


class Test_LedgerMicrosoftMoney(Basetest):
    """
    test Microsoft Money handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_msmoney2ledger(self):
        """
        test the Microsoft Money example
        """
        msmoney_example = Path(self.examples_path) / "sample_microsoft_money.zip"
        converter = MicrosoftMoneyToLedgerConverter(debug=self.debug)
        converter.load(msmoney_example)
        converter.log.do_print = self.debug
        book = converter.convert_to_target()
        converter.show_stats()
