"""
Created on 2024-10-03

@author: wf
"""

# expense_example.py
from pathlib import Path
from typing import Dict, Iterable

import requests
from lodstorage.persistent_log import Log

from nomina.gnucash import GncV2, GnuCashXml
from nomina.ledger import Book
from nomina.qif import SimpleQifParser
from nomina.stats import Stats


class NominaExample:
    """
    Nomina Example
    """

    def __init__(
        self,
        name: str,
        owner: str,
        url: str,
        example_path: Path,
        expected_stats: Stats,
        is_qif: bool = False,
        do_log: bool = False,
    ):
        self.name = name
        self.owner = owner
        self.url = url
        self.expected_stats = expected_stats
        # example paths
        self.example_path = example_path
        self.gnu_cash_xml_file = self.example_path / f"{name}_xml.gnucash"
        self.gnu_cash_sqlite_file = self.example_path / f"{name}_sqlite.gnucash"
        self.ledger_file = self.example_path / f"{self.name}.yaml"

        # parsers
        self.gcxml = GnuCashXml()
        self.sqp = SimpleQifParser()
        self.is_qif = is_qif
        # setup a persistent log
        self.plog = Log()
        self.plog.do_log = do_log

    def log(self, icon: str, kind: str, msg: str):
        """
        log to my persistent log
        """
        self.plog.log(icon=icon, kind=kind, msg=msg)

    @classmethod
    def get_examples(cls, do_log: bool = False) -> Dict[str, "NominaExample"]:
        examples = {}
        for name, owner, is_qif, url, expected_stats in [
            (
                "expenses",
                "Henning Jakobs",
                True,
                "https://raw.githubusercontent.com/hjacobs/gnucash-qif-import/refs/heads/master/examples/expenses.qif",
                Stats(
                    accounts=5,
                    transactions=2,
                    start_date="2014-01-02",
                    end_date="2014-01-02",
                    currencies={"EUR": 2},
                ),
            ),
            (
                "expenses2024",
                "Wolfgang Fahl",
                "",
                False,
                Stats(
                    accounts=3,
                    transactions=2,
                    start_date="2024-10-06",
                    end_date="2024-10-06",
                    currencies={"EUR": 2},
                ),
            ),
            (
                "simple_sample",
                "Sebastien de Menten",
                False,
                "https://github.com/sdementen/piecash/blob/master/gnucash_books/simple_sample.gnucash",
                Stats(
                    accounts=7,
                    transactions=5,
                    start_date="2014-11-30",
                    end_date="2014-12-24",
                    currencies={"EUR": 5},
                ),
            ),
            (
                "empty",
                "Wolfgang Fahl",
                False,
                None,
                Stats(
                    accounts=64,
                    transactions=0,
                    start_date=None,
                    end_date=None,
                    currencies={},
                ),
            ),
        ]:
            example_path = Path(__file__).parent.parent / "nomina_examples"
            example = NominaExample(
                name,
                owner,
                url,
                example_path,
                expected_stats,
                is_qif=is_qif,
                do_log=do_log,
            )
            examples[name] = example
        return examples

    def get_ledger_book(self) -> Book:
        """
        read the ledger book
        """
        ledger_book = Book.load_from_yaml_file(self.ledger_file)
        return ledger_book

    def get_parsed_qif(self) -> SimpleQifParser:
        """
        get the parsed QIF for the example
        """
        if self.url:
            self.qif = requests.get(self.url).text
            self.qif_lines = self.qif.splitlines()
        self.sqp.parse(self.qif_lines)
        return self.sqp

    def get_parsed_gnucash(self) -> GncV2:
        gncv2 = self.gcxml.parse_gnucash_xml(self.gnu_cash_xml_file)
        return gncv2

    def write_gnucash(self, gncv2: GncV2, base_path: str, suffix: str) -> Path:
        # Write the parsed data to a new XML file
        output_file = Path(f"{base_path}/{self.name}_{suffix}.gnucash")
        self.gcxml.write_gnucash_xml(gncv2, str(output_file))
        return output_file

    def check_file(self, file: Path):
        if not file.exists():
            self.log("❌", "file_existence", "File was not created.")
        elif file.stat().st_size == 0:
            self.log("❌", "file_size", "File is empty.")
        else:
            self.log("✅", "file_check", "File exists and is not empty.")

    def check_stats(self, stats: Stats, expected_stats: Stats = None) -> int:
        """
        Check the statistics using a simplified, recursive approach.
        """

        def compare(expected, actual, path=""):
            if isinstance(expected, dict) and isinstance(actual, dict):
                for k in set(expected) | set(actual):
                    yield from compare(
                        expected.get(k), actual.get(k), f"{path}.{k}" if path else k
                    )
            elif (
                isinstance(expected, Iterable)
                and isinstance(actual, Iterable)
                and not isinstance(expected, (str, bytes))
            ):
                if len(expected) != len(actual):
                    yield False, f"Length mismatch for {path}. Expected: {len(expected)}, Got: {len(actual)}"
                else:
                    for i, (e, a) in enumerate(zip(expected, actual)):
                        yield from compare(e, a, f"{path}[{i}]")
            elif expected != actual:
                yield False, f"Mismatch for {path}. Expected: {expected}, Got: {actual}"

        wrong = 0
        if expected_stats is None:
            expected_stats = self.expected_stats

        for attr in vars(expected_stats):
            expected_value = getattr(expected_stats, attr)
            actual_value = getattr(stats, attr)

            mismatches = list(compare(expected_value, actual_value, attr))

            if mismatches:
                for _, message in mismatches:
                    self.log("⚠️", f"{attr}_mismatch", message)
                    wrong += 1
            else:
                self.log("✅", f"{attr}_match", f"Match for {attr}")

        return wrong

    def expenses_qif(self) -> str:
        qif = """!Account
NExpenses:Dining
^
!Type:Cash

!Account
NCash in Wallet
^
!Type:Cash
D2014/1/2
MLunch at Marcy's
SExpenses:Dining
$-7.80
^


!Account
NCash in Wallet
^
!Type:Cash
D2014/1/2
MExpensive PC
SExpenses:Computer
ESome note
$-1234.56
^


!Account
NExpenses:Computer
^
!Type:Cash"""
        return qif
