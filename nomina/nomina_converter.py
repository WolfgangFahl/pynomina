"""
Created on 2024-10-06

@author: wf
"""

from typing import TextIO

from lodstorage.persistent_log import Log

from nomina.file_formats import AccountingFileFormat


class AccountingFileConverter:
    """
    Abstract base class for accounting file converters.
    This class provides a structure for converting accounting data from one format to another.
    """

    def __init__(
        self,
        from_format: AccountingFileFormat,
        to_format: AccountingFileFormat,
        debug: bool = False,
    ):
        """
        Constructor that initializes the log instance.
        """
        self.from_format = from_format
        self.to_format = to_format
        self.debug = debug
        self.source = None
        self.target = None
        self.log = Log()

    def convert(self, input_stream: TextIO, output_stream: TextIO) -> str:
        """
        Convert the input file to the target format.

        Args:
            input_stream (TextIO): File-like object to read from (can be a file or sys.stdin).
            output_stream (TextIO): File-like object to write to (can be a file or sys.stdout).

        Returns:
            str: The converted content in text format.
        """
        if self.debug:
            print(f"Loading {self.from_format.name} from {self.from_format.ext} file")
        self.source = self.load(input_stream)
        if self.debug:
            print(f"Converting {self.from_format.acronym} to {self.to_format.acronym}")
        self.target = self.convert_to_target()
        self.text = self.to_text()
        if output_stream:
            if self.debug:
                print(f"Writing {self.to_format.name} to {self.to_format.ext} file")
            output_stream.write(self.text)
        return self.text

    def show_stats(self):
        source_stats = self.source.get_stats()
        if self.debug:
            source_stats.show()
        target_stats = self.target.get_stats()
        if self.debug:
            target_stats.show()

    def load(self, input_stream: TextIO):
        """
        Load the content from the input stream.

        Args:
            input_stream (str): The input stream

        Raises:
            ValueError: If called on the abstract base class.
        """
        raise ValueError("load must be implemented in the subclass")

    def convert_to_target(self) -> object:
        """
        Convert the loaded source content to the target format.

        Returns:
            object: The converted content object (could be any personal accounting book type).
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
