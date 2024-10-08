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
from nomina.qif_ledger import QifToLedgerConverter


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
            "LB-YAML": None,
        }
        self.from_ledger = {
            "GC-XML": LedgerToGnuCashConverter,
            "BEAN": LedgerToBeancountConverter,
            "LB-YAML": None,
        }

    def copy(self, source_path: str, destination: TextIO):
        """
        Copy the content from source_path to destination stream
        """
        with open(source_path, "r") as source_file:
            content=source_file.read()
            destination.write(content)


    def convert(self, input_path: str = None, output_format: str = None):
        """
        Convert the input file to the specified output format as specified in the
        command line arguments
        """
        if input_path is None:
            input_path=self.args.convert
        if output_format is None:
            output_format = self.args.format
        input_format = self.detector.detect_format(input_path)

        if not input_format:
            raise ValueError(
                f"Unsupported or unrecognized input format for file: {input_path}"
            )

        if input_format.acronym not in self.to_ledger:
            raise ValueError(f"Unsupported input format: {input_format.acronym}")
        if output_format not in self.from_ledger:
            raise ValueError(f"Unsupported output format: {output_format}")

        to_ledger_cls = self.to_ledger.get(input_format.acronym)
        from_ledger_cls = self.from_ledger.get(output_format)

        if not to_ledger_cls:
            ledger_file_path=input_path
        else:
            to_ledger = to_ledger_cls(debug=self.args.debug)
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml") as ledger_file:
                to_ledger.convert(input_path, ledger_file)
                ledger_file.seek(0)  # Reset file pointer to beginning
                ledger_file_path=ledger_file.name


        if not from_ledger_cls:
            self.copy(ledger_file_path,self.args.output)
        else:
            from_ledger = from_ledger_cls(debug=self.args.debug)
            from_ledger.convert(ledger_file_path, self.args.output)



    def get_supported_formats(self):
        """
        Get a list of supported input and output formats
        """
        input_formats = set(self.to_ledger.keys())
        output_formats = set(self.from_ledger.keys())
        return {"input": list(input_formats), "output": list(output_formats)}
