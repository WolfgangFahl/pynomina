"""
Created on 2024-10-06

@author: wf
"""

import tempfile
from typing import TextIO

from nomina.beancount_ledger import (
    BeancountToLedgerConverter,
    LedgerToBeancountConverter,
)
from nomina.bzv_ledger import BankingZVToLedgerConverter
from nomina.file_formats import AccountingFileFormats
from nomina.gnc_ledger import GnuCashToLedgerConverter, LedgerToGnuCashConverter
from nomina.nomina_converter import AccountingFileConverter
from nomina.qif_ledger import QifToLedgerConverter


class IdentityConverter(AccountingFileConverter):
    """
    Dummy converter for hub&spoke
    """

    def convert(self, input_stream: TextIO, output_stream: TextIO) -> str:
        content = input_stream.read()
        if output_stream:
            output_stream.write(content)
        return content


class Converter:
    """
    General converter for personal accounting formats using hub and spoke model
    """

    def __init__(self, args):
        self.args = args
        self.detector = AccountingFileFormats()
        self.to_ledger = {
            "GC-XML": GnuCashToLedgerConverter,
            "QIF": QifToLedgerConverter,
            "BEAN": BeancountToLedgerConverter,
            "BZV-YAML": BankingZVToLedgerConverter,
            "LB-YAML": IdentityConverter,
        }
        self.from_ledger = {
            "GC-XML": LedgerToGnuCashConverter,
            "BEAN": LedgerToBeancountConverter,
            "LB-YAML": IdentityConverter,
        }

    def convert(self, input_file: str = None, output_format: str = None):
        """
        Convert the input file to the specified output format as specified in the
        command line arguments
        """
        if input_file is None:
            input_file = self.args.convert
        if output_format is None:
            output_format = self.args.format
        input_format = self.detector.detect_format(input_file)

        if not input_format:
            raise ValueError(
                f"Unsupported or unrecognized input format for file: {input_file}"
            )

        to_ledger = self.to_ledger.get(input_format.acronym)
        from_ledger = self.from_ledger.get(output_format)

        if not to_ledger:
            raise ValueError(f"Unsupported input format: {input_format.acronym}")
        if not from_ledger:
            raise ValueError(f"Unsupported output format: {output_format}")

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml") as ledger_file:
            to_ledger = to_ledger(
                debug=self.args.debug
            )
            from_ledger = from_ledger(
                debug=self.args.debug,
            )

            to_ledger.convert(input_file, ledger_file)
            ledger_file.seek(0)  # Reset file pointer to beginning
            from_ledger.convert(ledger_file, self.args.output)

    def get_supported_formats(self):
        """
        Get a list of supported input and output formats
        """
        input_formats = set(self.to_ledger.keys())
        output_formats = set(self.from_ledger.keys())
        return {"input": list(input_formats), "output": list(output_formats)}
