"""
Created on 2024-10-06

@author: wf
"""

from typing import Optional, TextIO

from lodstorage.persistent_log import Log

from nomina.file_formats import AccountingFileFormat, AccountingFileFormats
from nomina.ledger import Book


class AccountingFileConverter:
    """
    Abstract base class for accounting file converters.
    This class provides a structure for converting accounting data from one format to another.
    """

    def __init__(
        self,
        from_format_acronym: str,
        to_format_acronym: str,
        debug: bool = False,
    ):
        """
        Constructor that initializes the converter instance.

        Args:
            from_format_acronym (str): Acronym of the source format
            to_format_acronym (str): Acronym of the target format
            debug (bool): If True, enable debug output
        """
        formats = AccountingFileFormats()
        self.from_format: AccountingFileFormat = formats.get_by_acronym(
            from_format_acronym
        )
        self.to_format: AccountingFileFormat = formats.get_by_acronym(to_format_acronym)
        self.debug: bool = debug
        self.source: Optional[object] = None
        self.target: Optional[object] = None
        self.log: Log = Log()

    def load(self, input_stream: TextIO) -> object:
        """
        Load the content from the input stream.

        Args:
            input_stream (TextIO): The input stream

        Returns:
            object: The loaded content

        Raises:
            ValueError: If called on the abstract base class.
        """
        raise ValueError("load must be implemented in the subclass")

    def convert_to_target(self) -> object:
        """
        Convert the loaded source content to the target format.

        Returns:
            object: The converted content object (could be any personal accounting book type).

        Raises:
            ValueError: If called on the abstract base class.
        """
        raise ValueError("convert_to_target must be implemented in the subclass")

    def to_text(self) -> str:
        """
        Convert the target object into a text representation.

        Returns:
            str: The text representation of the target content.

        Raises:
            ValueError: If not implemented by a subclass.
        """
        raise ValueError("to_text must be implemented in the subclass")

    def show_stats(self) -> None:
        """
        Display statistics about the source and target objects.
        """
        source_stats = self.source.get_stats()
        if self.debug:
            source_stats.show()
        target_stats = self.target.get_stats()
        if self.debug:
            target_stats.show()


class BaseToLedgerConverter(AccountingFileConverter):
    """
    Base class for converters that convert from various formats to LedgerBook format.
    """

    def __init__(self, from_format_acronym: str, debug: bool = False):
        """
        Constructor for BaseToLedgerConverter.

        Args:
            from_format_acronym (str): Acronym of the source format
            debug (bool): If True, enable debug output
        """
        super().__init__(from_format_acronym, "LB-YAML", debug)

    def convert_to_ledger(self, input_path: str) -> Book:
        """
        Convert the input file to LedgerBook format.

        Args:
            input_path (str): Path to the input file

        Returns:
            Book: The converted LedgerBook object
        """
        if self.debug:
            print(f"Loading {self.from_format.name} from {input_path}")
        self.source = self.load(input_path)
        if self.debug:
            print(f"Converting {self.from_format.acronym} to {self.to_format.acronym}")
        self.target = self.convert_to_target()
        self.show_stats()
        return self.target


class BaseFromLedgerConverter(AccountingFileConverter):
    """
    Base class for converters that convert from LedgerBook format to various formats.
    """

    def __init__(self, to_format_acronym: str, debug: bool = False):
        """
        Constructor for BaseFromLedgerConverter.

        Args:
            to_format_acronym (str): Acronym of the target format
            debug (bool): If True, enable debug output
        """
        super().__init__("LB-YAML", to_format_acronym, debug)

    def convert_from_ledger(self, ledger_book: Book) -> object:
        """
        Convert from LedgerBook format to the target format object.

        Args:
            ledger_book (Book): The LedgerBook object to convert

        Returns:
            object: The converted object in the target format
        """
        self.set_source(ledger_book)
        if self.debug:
            print(
                f"Converting Ledger Book {ledger_book.name} to {self.to_format.acronym}"
            )
        self.target = self.convert_to_target()
        self.show_stats()
        return self.target

    def to_text(self, target: object) -> str:
        """
        Convert the target object into a text representation.

        Args:
            target (object): The target object to convert to text

        Returns:
            str: The text representation of the target content.

        Raises:
            ValueError: If not implemented by a subclass.
        """
        raise ValueError("to_text must be implemented in the subclass")
