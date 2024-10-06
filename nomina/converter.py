"""
Created on 2024-10-06

@author: wf
"""

from nomina.file_formats import AccountingFileFormatDetector
from nomina.gnc_ledger import GnuCashToLedgerConverter, LedgerToGnuCashConverter
from nomina.qif_ledger import QifToLedgerConverter


class Converter:
    """
    general converter for personal accounting formats
    """

    def __init__(self):
        self.detector = AccountingFileFormatDetector()
        self.converters = {
            ("LB-YAML", "gcxml"): LedgerToGnuCashConverter(),
            ("GC-XML", "ledger"): GnuCashToLedgerConverter(),
            ("QIF", "ledger"): QifToLedgerConverter(),
        }

    def convert(self, input_file, output_format: str):
        """
        Convert the input file to the specified output format
        """
        input_format = self.detector.detect_format(input_file)

        if not input_format:
            raise ValueError(
                f"Unsupported or unrecognized input format for file: {input_file}"
            )

        converter = self.converters.get((input_format.acronym, output_format))
        if not converter:
            raise ValueError(
                f"Unsupported conversion: {input_format.acronym} to {output_format}"
            )

        return converter.convert(input_file)
