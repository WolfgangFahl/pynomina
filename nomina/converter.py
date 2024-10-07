"""
Created on 2024-10-06

@author: wf
"""

from nomina.beancount_ledger import (
    BeancountToLedgerConverter,
    LedgerToBeancountConverter,
)
from nomina.bzv_ledger import BankingZVToLedgerConverter
from nomina.file_formats import AccountingFileFormatDetector
from nomina.gnc_ledger import GnuCashToLedgerConverter, LedgerToGnuCashConverter
from nomina.qif_ledger import QifToLedgerConverter
from nomina.nomina_converter import AccountingFileConverter

class IdentityConverter(AccountingFileConverter):
    def convert(self, input_file):
        return input_file

class Converter:
    """
    General converter for personal accounting formats using hub and spoke model
    """

    def __init__(self):
        self.detector = AccountingFileFormatDetector()
        self.to_ledger = {
            "GC-XML": GnuCashToLedgerConverter,
            "QIF": QifToLedgerConverter,
            "BEAN": BeancountToLedgerConverter,
            "BZV-JSON": BankingZVToLedgerConverter,
            "LB-YAML": IdentityConverter,
        }
        self.from_ledger = {
            "GC-XML": LedgerToGnuCashConverter,
            "BEAN": LedgerToBeancountConverter,
            "LB-YAML": IdentityConverter
        }

    def convert(self, input_file, output_format: str):
        """
        Convert the input file to the specified output format
        """
        input_format = self.detector.detect_format(input_file)

        if not input_format:
            raise ValueError(f"Unsupported or unrecognized input format for file: {input_file}")

        to_ledger = self.to_ledger.get(input_format.acronym)
        from_ledger = self.from_ledger.get(output_format)

        if not to_ledger:
            raise ValueError(f"Unsupported input format: {input_format.acronym}")
        if not from_ledger:
            raise ValueError(f"Unsupported output format: {output_format}")

        # Lazy initialization: only create converter instances when needed
        to_ledger = to_ledger()
        from_ledger = from_ledger()

        ledger_book = to_ledger.convert(input_file)
        return from_ledger.convert(ledger_book)

    def get_supported_formats(self):
        """
        Get a list of supported input and output formats
        """
        input_formats = set(self.to_ledger.keys())
        output_formats = set(self.from_ledger.keys())
        return {"input": list(input_formats), "output": list(output_formats)}
