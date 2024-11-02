"""
Created on 2024-10-06

@author: wf
"""

import os
import re
import zipfile
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
    pattern_file: Optional[str] = None
    encoding: str = "utf-8"


class AccountingFileFormats:
    """
    Detector for various accounting file formats
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
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
                name="Microsoft Money - Zipped JSON dumps",
                acronym="MS-MONEY-ZIP",
                ext=".zip",
                wikidata_id="Q117428",
                pattern_file="nomina.yaml",
                content_pattern=r"NOMINA-MICROSOFT-MONEY-YAML",
                encoding="utf-8",
            ),
            AccountingFileFormat(
                name="Microsoft Money",
                acronym="MS-MONEY",
                ext=".mny",
                wikidata_id="Q117428",
                content_pattern=r"",
                encoding="utf-8",
            ),
            AccountingFileFormat(
                name="pyNomina Ledger Book YAML",
                acronym="LB-YAML",
                ext=".yaml",
                wikidata_id="Q281876",
                content_pattern=r"file_type:\s*NOMINA-LEDGER-BOOK-YAML",
            ),
            AccountingFileFormat(
                name="FinanzmanagerDeluxe",
                acronym="FMD",
                ext=".qif",
                wikidata_id="Q750657",
                content_pattern=r"!Option:MDY",
                encoding="iso-8859-1",
            ),
            AccountingFileFormat(
                name="Quicken Interchange Format",
                acronym="QIF",
                ext=".qif",
                wikidata_id="Q750657",
                content_pattern=r"(?:\^.*?){5}",  # at least five ^ entries
            ),
            AccountingFileFormat(
                name="Subsembly JSON",
                acronym="BZV-JSON",
                ext=".json",
                wikidata_id="Q130443951",
                content_pattern=r'"AcctId":\s*"[^"]+".*"OwnrAcctCcy":\s*"[^"]+"',
            ),
            AccountingFileFormat(
                name="pyNomina Banking ZV YAML export",
                acronym="BZV-YAML",
                ext=".yaml",
                wikidata_id="Q281876",
                content_pattern=r"account_json_exports\s*:",
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

        if file_extension.lower() == ".zip":
            return self._detect_from_zip(file_path)
        else:
            return self._detect_from_regular_file(file_path)

    def _detect_from_zip(self, zip_path: str) -> Optional[AccountingFileFormat]:
        """
        Detect accounting file format by looking inside the zip file.
        """
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            for fformat in self.formats:
                # Check if the format has a pattern_file defined
                if (
                    fformat.ext == ".zip"
                    and fformat.pattern_file in zip_file.namelist()
                ):
                    content = self._extract_file_content_from_zip(
                        zip_file, fformat.pattern_file
                    )
                    if content and self._match_pattern(
                        content, fformat.content_pattern
                    ):
                        return fformat
        return None

    def _extract_file_content_from_zip(
        self, zip_file: zipfile.ZipFile, pattern_file: str
    ) -> Optional[str]:
        """
        Extract the content of a specific file within a zip and decode it.
        """
        with zip_file.open(pattern_file) as file:
            raw_data = file.read()
            return self._decode_content(raw_data)

    def _detect_from_regular_file(
        self, file_path: str
    ) -> Optional[AccountingFileFormat]:
        """
        Detect accounting file format from a regular non-zip file.
        """
        with open(file_path, "rb") as file:
            raw_data = file.read(10000)  # Read the first 10000 bytes
            content = self._decode_content(raw_data)

        if content:
            for fformat in self.formats:
                _name, ext = os.path.splitext(file_path)
                if ext.lower() == fformat.ext.lower():
                    match = self._match_pattern(content, fformat.content_pattern)
                    if match:
                        return fformat
        return None

    def _decode_content(self, raw_data: bytes) -> Optional[str]:
        """
        Detect the encoding of the raw data and decode it into a string.
        """
        result = chardet.detect(raw_data)
        encoding = result.get("encoding", "utf-8")
        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError:
            return raw_data.decode("latin-1", errors="ignore")

    def _match_pattern(self, content: str, pattern: str) -> bool:
        """
        Check if the content matches the given pattern.
        """
        return bool(re.search(pattern, content, re.DOTALL | re.IGNORECASE))
