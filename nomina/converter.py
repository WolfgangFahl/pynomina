"""
Created on 2024-10-06

@author: wf
"""

from pathlib import Path
from typing import Dict, Type

from nomina.beancount_ledger import (
    BeancountToLedgerConverter,
    LedgerToBeancountConverter,
)
from nomina.bzv_ledger import BankingZVToLedgerConverter
from nomina.file_formats import AccountingFileFormats
from nomina.gnc_ledger import GnuCashToLedgerConverter, LedgerToGnuCashConverter
from nomina.ledger import Book
from nomina.msmoney_ledger import MicrosoftMoneyToLedgerConverter
from nomina.nomina_converter import BaseFromLedgerConverter, BaseToLedgerConverter
from nomina.qif_ledger import QifToLedgerConverter


class Converter:
    """
    General converter for personal accounting formats using hub and spoke model
    """

    def __init__(self, args):
        self.args = args
        self.detector = AccountingFileFormats()
        self.to_ledger: Dict[str, Type[BaseToLedgerConverter]] = {
            "GC-XML": GnuCashToLedgerConverter,
            "QIF": QifToLedgerConverter,
            "BEAN": BeancountToLedgerConverter,
            "BZV-YAML": BankingZVToLedgerConverter,
            "MONEY": MicrosoftMoneyToLedgerConverter,
            "LB-YAML": None,
        }
        self.from_ledger: Dict[str, Type[BaseFromLedgerConverter]] = {
            "GC-XML": LedgerToGnuCashConverter,
            "BEAN": LedgerToBeancountConverter,
            "LB-YAML": None,
        }

    def convert(self, input_path: Path = None, output_format: str = None) -> None:
        """
        Convert the input file to the specified output format.

        Args:
            input_path (str, optional): Path to the input file. Defaults to None.
            output_format (str, optional): Acronym of the output format. Defaults to None.
        """
        if input_path is None:
            input_path = self.args.convert
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

        to_ledger_cls = self.to_ledger[input_format.acronym]
        from_ledger_cls = self.from_ledger[output_format]

        # Convert to LedgerBook
        if to_ledger_cls is not None:
            to_ledger = to_ledger_cls(debug=self.args.debug)
            ledger_book = to_ledger.convert_to_ledger(input_path)
        else:
            # If input is already LedgerBook, just load it
            ledger_book = Book.load_from_yaml_file(input_path)

        # Convert from LedgerBook to output format
        if from_ledger_cls is not None:
            from_ledger = from_ledger_cls(debug=self.args.debug)
            _target_object = from_ledger.convert_from_ledger(ledger_book)
            output_text = from_ledger.to_text()
            pass
        else:
            # target is a LedgerBook get the XML markup
            output_text = ledger_book.to_yaml()
        output_stream = self.args.output.open("w")
        output_stream.write(output_text)
        output_stream.close()

    def get_supported_formats(self) -> Dict[str, list]:
        """
        Get a list of supported input and output formats

        Returns:
            Dict[str, list]: A dictionary with 'input' and 'output' keys, each containing a list of supported format acronyms
        """
        input_formats = set(self.to_ledger.keys())
        output_formats = set(self.from_ledger.keys())
        return {"input": list(input_formats), "output": list(output_formats)}
