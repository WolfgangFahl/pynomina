"""
Created on 2026-10-19

@author: wf

VAT codes of Finanzmanager Deluxe QIF exports, see issue #16
"""

import os
import tempfile

from nomina.beancount_ledger import LedgerToBeancountConverter
from nomina.qif_ledger import QifToLedgerConverter
from nomina.vat_codes import VatCode, VatCodes, VatRate
from tests.basetest import Basetest

VAT_SAMPLE = """!Option:MDY
!Type:Cat
NFirma
DFirma
E
^
NFirmeneinnahmen
DFirmeneinnahmen
I
^
!Account
NMehrwertsteuer
TOth L
^
!Account
NGiro
TBank
^
!Type:Bank
D1.4.00
U25.54
T25.54
PKunde
MRechnung 1
LFirmeneinnahmen
SFirmeneinnahmen
$22.02
S[Mehrwertsteuer]/_VATCode_N1_O
$3.52
^
D1.5.00
U-28.75
T-28.75
PLieferant
MRechnung 2
LFirma
SFirma
$-24.78
S[Mehrwertsteuer]/_VATCode_N1_I
$-3.97
^
D1.6.00
U-11.90
T-11.90
PLieferant
MRechnung 3
LFirma
SFirma
$-10.00
S[Mehrwertsteuer]/_VATCode_X9_I
$-1.90
^
"""


class TestVatCodes(Basetest):
    """
    test VAT code handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.tmp = tempfile.NamedTemporaryFile(
            "w", suffix=".qif", delete=False, encoding="iso-8859-1"
        )
        self.tmp.write(VAT_SAMPLE)
        self.tmp.close()

    def tearDown(self):
        Basetest.tearDown(self)
        os.unlink(self.tmp.name)

    def vat_splits(self, book) -> dict:
        """
        get the splits with a VAT code by transaction memo
        """
        vat_splits = {}
        for tx in book.transactions.values():
            for split in tx.splits:
                if split and split.vat_code:
                    vat_splits[tx.memo] = split
        return vat_splits

    def test_default_map(self):
        """
        the default map knows the measured codes and their dated rates
        """
        vat_codes = VatCodes.of_yaml()
        for code in ["N", "N1", "H", "7", "B", "2"]:
            self.assertIsNotNone(vat_codes.lookup(code), code)
        n1 = vat_codes.lookup("N1")
        self.assertEqual(16.0, n1.rate_for("2000-01-04").rate)
        self.assertEqual(16.0, n1.rate_for("2020-10-01").rate)
        self.assertIsNone(n1.rate_for("2015-01-01"))
        self.assertEqual(19.0, vat_codes.lookup("N").rate_for("2015-01-01").rate)
        self.assertIsNone(vat_codes.lookup("2").rate_for(None).rate)

    def test_parse(self):
        """
        class markup is split into code and direction
        """
        self.assertEqual(("N1", "I"), VatCodes.parse("_VATCode_N1_I"))
        self.assertEqual(("7", "I"), VatCodes.parse("_VATCode_7_I"))
        self.assertEqual(("B", "O"), VatCodes.parse("_VATCode_B_O"))
        self.assertIsNone(VatCodes.parse("MKOP:Gruppe21"))
        self.assertIsNone(VatCodes.parse(None))

    def test_qif_conversion(self):
        """
        the VAT code is kept on the split and not in the memo
        """
        converter = QifToLedgerConverter()
        book = converter.convert_to_ledger(self.tmp.name)
        vat_splits = self.vat_splits(book)
        if self.debug:
            print(vat_splits)
        self.assertEqual("N1_O", vat_splits["Rechnung 1"].vat_code)
        self.assertEqual("N1_I", vat_splits["Rechnung 2"].vat_code)
        self.assertAlmostEqual(-3.52, vat_splits["Rechnung 1"].amount, places=2)
        self.assertNotIn("_VATCode_", vat_splits["Rechnung 1"].memo or "")

    def test_unknown_code(self):
        """
        an unknown code is kept and reported
        """
        converter = QifToLedgerConverter()
        book = converter.convert_to_ledger(self.tmp.name)
        self.assertEqual("X9_I", self.vat_splits(book)["Rechnung 3"].vat_code)
        warnings = [e for e in converter.log.entries if e.kind == "vat_code"]
        self.assertEqual(1, len(warnings))
        self.assertIn("X9", warnings[0].msg)

    def test_user_map(self):
        """
        a user map replaces the default map
        """
        user_map = VatCodes(
            name="user",
            codes={"X9": VatCode(code="X9", rates=[VatRate(rate=19.0)])},
        )
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(user_map.to_yaml())
        vat_codes = VatCodes.of_yaml(f.name)
        os.unlink(f.name)
        converter = QifToLedgerConverter(vat_codes=vat_codes)
        converter.convert_to_ledger(self.tmp.name)
        warnings = [e for e in converter.log.entries if e.kind == "vat_code"]
        # N1 is unknown in the user map, X9 is known
        self.assertEqual(2, len(warnings))
        self.assertTrue(all("N1" in w.msg for w in warnings))

    def test_beancount_metadata(self):
        """
        the VAT code is written as beancount posting metadata
        """
        book = QifToLedgerConverter().convert_to_ledger(self.tmp.name)
        to_bean = LedgerToBeancountConverter()
        to_bean.convert_from_ledger(book)
        text = to_bean.to_text()
        if self.debug:
            print(text)
        self.assertIn('vat_code: "N1_O"', text)
        self.assertIn('vat_code: "N1_I"', text)
