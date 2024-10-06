"""
Created on 2024-10-06

@author: wf
"""

import os
import re
from dataclasses import dataclass
from typing import List, Optional

import chardet


@dataclass
class AccountingFileFormat:
    """
    A personal account file format
    """

    name: str
    acronym: str
    ext: str
    wikidata_id: str
    content_pattern: str


class AccountingFileFormatDetector:
    """
    Detector for various accounting file formats
    """

    def __init__(self):
        self.formats: List[AccountingFileFormat] = [
            AccountingFileFormat(
                name="Quicken Interchange Format",
                acronym="QIF",
                ext=".qif",
                wikidata_id="Q750657",
                content_pattern=r"!Account.*!Type:Cash",
            ),
            AccountingFileFormat(
                "Subsembly JSON",
                "BZV-JSON",
                ".json",
                "Q130443951",
                content_pattern=r'"AcctId":\s*"\d+".*"OwnrAcctCcy":\s*"\w+"',
            ),
            AccountingFileFormat(
                "GnuCash XML",
                "GC-XML",
                ".gnucash",
                "Q130445392",
                content_pattern=r"<gnc-v2",
            ),
            AccountingFileFormat(
                "pyNomina Ledger Book YAML",
                "LB-YAML",
                ".yaml",
                "Q281876",
                content_pattern=r"file_type:\s*NOMINA-LEDGER-BOOK-YAML\s*version:\s*0\.1",
            ),
        ]

    def detect_format(self, file_path: str) -> Optional[AccountingFileFormat]:
        """
        Detect the accounting file format based on content and extension
        """
        _, file_extension = os.path.splitext(file_path)
        # Read the first chunk of the file
        with open(file_path, "rb") as file:
            raw_data = file.read(10000)  # Read first 10000 bytes

        # Detect encoding
        result = chardet.detect(raw_data)
        encoding = result["encoding"]

        # Decode the raw data
        try:
            content = raw_data.decode(encoding)
        except UnicodeDecodeError:
            # If the detected encoding fails, fall back to latin-1
            content = raw_data.decode("latin-1")

        for fformat in self.formats:
            if file_extension.lower() == fformat.ext.lower() and re.search(
                fformat.content_pattern, content, re.DOTALL | re.IGNORECASE
            ):
                return fformat

        return None

    def get_format_by_extension(self, file_path: str) -> Optional[AccountingFileFormat]:
        """
        Get the accounting file format based on file extension only
        """
        _, file_extension = os.path.splitext(file_path)

        for format in self.formats:
            if file_extension.lower() == format.ext.lower():
                return format

        return None
