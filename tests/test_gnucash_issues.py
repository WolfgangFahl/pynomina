"""
Created on 2026-10-19

@author: wf

GnuCash issues #31 gzipped files and #32 bookings with same date and description
"""

import gzip
import os
import re
import tempfile

from nomina.beancount_ledger import (
    BeancountToLedgerConverter,
    LedgerToBeancountConverter,
)
from nomina.file_formats import AccountingFileFormats
from nomina.gnc_ledger import GnuCashToLedgerConverter
from tests.basetest import Basetest


class TestGnuCashIssues(Basetest):
    """
    test gzipped GnuCash XML and non unique transaction descriptions
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        examples = os.path.join(os.path.dirname(__file__), "../nomina_examples")
        with open(os.path.join(examples, "expenses_xml.gnucash"), "rb") as f:
            self.xml_bytes = f.read()
        self.tmp_paths = []

    def tearDown(self):
        Basetest.tearDown(self)
        for path in self.tmp_paths:
            os.unlink(path)

    def write_tmp(self, content: bytes) -> str:
        """
        write the given content to a temporary .gnucash file
        """
        with tempfile.NamedTemporaryFile(suffix=".gnucash", delete=False) as f:
            f.write(content)
        self.tmp_paths.append(f.name)
        return f.name

    def test_gzipped_gnucash(self):
        """
        issue #31: GnuCash saves compressed XML with the same extension
        """
        path = self.write_tmp(gzip.compress(self.xml_bytes))
        fformat = AccountingFileFormats().detect_format(path)
        self.assertIsNotNone(fformat)
        self.assertEqual("GC-XML", fformat.acronym)
        book = GnuCashToLedgerConverter().convert_to_ledger(path)
        self.assertEqual(2, len(book.transactions))

    def test_same_date_and_description(self):
        """
        issue #32: bookings with the same date and description are all kept
        """
        xml = self.xml_bytes.decode("utf-8")
        match = re.search(r"<gnc:transaction.*?</gnc:transaction>", xml, re.DOTALL)
        trn = match.group(0)
        guid = re.search(r'<trn:id type="guid">([0-9a-f]+)</trn:id>', trn).group(1)
        twin = trn.replace(guid, "f" * len(guid))
        xml = xml.replace(trn, trn + "\n" + twin, 1)
        path = self.write_tmp(xml.encode("utf-8"))
        book = GnuCashToLedgerConverter().convert_to_ledger(path)
        self.assertEqual(3, len(book.transactions))
        to_bean = LedgerToBeancountConverter()
        to_bean.convert_from_ledger(book)
        text = to_bean.to_text()
        bean_path = self.write_tmp(text.encode("utf-8"))
        bean_book = BeancountToLedgerConverter().convert_to_ledger(bean_path)
        self.assertEqual(3, len(bean_book.transactions))
