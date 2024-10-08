"""
Created on 2024-10-06

@author: wf
"""

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

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


class AccountingFileFormats:
    """
    Detector for various accounting file formats
    """

    def __init__(self):
        self.formats: List[AccountingFileFormat] = [
            AccountingFileFormat(
                name="Beancount",
                acronym="BEAN",
                ext=".beancount",
                wikidata_id="Q130456404",
                content_pattern=r'option "title"',
            ),
            AccountingFileFormat(
                name="GnuCash XML",
                acronym="GC-XML",
                ext=".gnucash",
                wikidata_id="Q130445392",
                content_pattern=r"<gnc-v2",
            ),
            AccountingFileFormat(
                name="GnuCash SQLite",
                acronym="GC-SQLITE",
                ext=".gnucash",
                wikidata_id="Q130445392",
                content_pattern=r"SQLite format 3",
            ),
            AccountingFileFormat(
                name="pyNomina Ledger Book YAML",
                acronym="LB-YAML",
                ext=".yaml",
                wikidata_id="Q281876",
                content_pattern=r"file_type:\s*NOMINA-LEDGER-BOOK-YAML|accounts:\s*\w+:",
            ),
            AccountingFileFormat(
                name="Quicken Interchange Format",
                acronym="QIF",
                ext=".qif",
                wikidata_id="Q750657",
                content_pattern=r"!Account.*!Type:Cash",
            ),
            AccountingFileFormat(
                name="Subsembly JSON",
                acronym="BZV-JSON",
                ext=".json",
                wikidata_id="Q130443951",
                content_pattern=r'"AcctId":\s*"[^"]+".*"OwnrAcctCcy":\s*"[^"]+"',
            ),
        ]
        self.format_by_acronym: Dict[str, AccountingFileFormat] = {
            fformat.acronym: fformat for fformat in self.formats
        }

    def get_by_acronym(self, acronym: str) -> "AccountingFileFormat":
        """
        get format by acronym
        """
        return self.format_by_acronym.get(acronym)

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
