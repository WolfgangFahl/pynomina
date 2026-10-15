"""
Created on 2026-10-15

@author: wf

Finanzmanager Deluxe exports: !Option:MDY dates and split lines, see issue #33
"""

import os
import tempfile

from nomina.qif import SimpleQifParser
from nomina.qif_ledger import QifToLedgerConverter
from tests.basetest import Basetest

FMD_SAMPLE = """!Option:MDY
!Type:Class
NMKOP
DMarketing Operations
^
!Account
NKasse
TBar
^
!Type:Bar
D7.10.00
U-88.45
T-88.45
CX
PPalmConsult Markus Reichart
MRe. RE0001881 v. 10.07.2000
L4980 Betriebsausstattung/MKOP:Gruppe21:DMS EXPO2001
S4980 Betriebsausstattung/MKOP:Gruppe21:DMS EXPO2001
EPalm Zubehör
$-44.22
S4980 Betriebsausstattung/BITPlan:Büroausstattung
$-44.23
^
D12.24.01
U-5.00
T-5.00
PPost
L4910 Porto
^
"""


class TestQifFmd(Basetest):
    """
    test Finanzmanager Deluxe QIF handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.tmp = tempfile.NamedTemporaryFile(
            "w", suffix=".qif", delete=False, encoding="iso-8859-1"
        )
        self.tmp.write(FMD_SAMPLE)
        self.tmp.close()

    def tearDown(self):
        Basetest.tearDown(self)
        os.unlink(self.tmp.name)

    def test_mdy_dates(self):
        """
        !Option:MDY means month first: D7.10.00 is 2000-07-10, D12.24.01 is 2001-12-24
        """
        parser = SimpleQifParser()
        parser.parse_file(self.tmp.name)
        dates = sorted(tx.isodate for tx in parser.transactions.values())
        self.assertEqual(["2000-07-10", "2001-12-24"], dates)

    def test_split_lines(self):
        """
        S, E and $ lines become one ledger split each, with the class in the memo
        """
        converter = QifToLedgerConverter()
        book = converter.convert_to_ledger(self.tmp.name)
        palm = [t for t in book.transactions.values() if "RE0001881" in str(t.memo)]
        self.assertEqual(1, len(palm))
        splits = palm[0].splits
        if self.debug:
            print(splits)
        self.assertEqual(3, len(splits))
        self.assertAlmostEqual(-88.45, splits[0].amount, places=2)
        self.assertAlmostEqual(44.22, splits[1].amount, places=2)
        self.assertAlmostEqual(44.23, splits[2].amount, places=2)
        self.assertIn("MKOP:Gruppe21:DMS EXPO2001", splits[1].memo)
        self.assertTrue(splits[1].account_id.endswith("4980 Betriebsausstattung"))
