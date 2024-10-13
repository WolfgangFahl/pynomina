"""
Created on 2024-10-01

Quicken Interchange Format (QIF) Parser
see https://en.wikipedia.org/wiki/Quicken_Interchange_Format


@author: wf
"""

import logging
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from lodstorage.yamlable import lod_storable

from nomina.date_utils import DateUtils
from nomina.stats import Stats


@dataclass
class ParseRecord:
    """
    generic parse record to keep track of lines and errors
    """

    start_line: int = 0
    end_line: int = 0
    errors: Dict[str, Exception] = field(default_factory=dict)


@dataclass
class SplitCategory:
    """
    a Quicken Interchange Format (QIF) Split target
    """

    markup: str  # the original QIF markup for the split category
    # parts of split
    category: Optional[str] = None
    account: Optional[str] = None
    split_class: Optional[str] = None
    # flags
    has_pipe: bool = False
    has_slash: bool = False

    def __post_init__(self):
        """
        parse my target string
        """
        self.has_pipe = "|" in self.markup
        self.has_slash = "/" in self.markup
        # qif holds the markup which still needs processing
        qif = self.markup

        pattern = r"\[(?P<account_name>[^\]]+)\]"

        # Search for the pattern in the split_category string
        match = re.search(pattern, self.markup)

        if match:
            # Extract the account name from the named group
            self.account = match.group("account_name")
            qif = qif.replace(f"[{self.account}]", "")
        else:
            self.account = None

        if self.has_pipe:
            qif = qif.replace("|", "")

        if self.has_slash:
            # Split by the first slash to separate category and class
            parts = qif.split("/", 1)
            if len(parts) > 1:
                # If there's a class after the slash, set it
                self.split_class = parts[1]
                qif = parts[0]
        if qif:
            self.category = qif


@lod_storable
class ErrorRecord(ParseRecord):
    line: Optional[str] = None


@lod_storable
class Category(ParseRecord):
    """
    a QIF tag (Class or Category)
    """

    name: Optional[str] = None
    description: str = ""


@lod_storable
class QifClass(ParseRecord):
    """
    a QIF tag (Class or Category)
    """

    name: Optional[str] = None
    description: str = ""


@lod_storable
class Account(ParseRecord):
    name: Optional[str] = None
    description: str = ""
    account_type: Optional[str] = None
    # note https://github.com/codinguser/gnucash-android/issues/218
    currency: str = "EUR"  # Default to EUR
    parent_account_id: Optional[str] = None


@lod_storable
class Transaction(ParseRecord):
    """
    a single transaction
    """

    isodate: Optional[str] = None
    amount: Optional[str] = None
    name: Optional[str] = None  # Vorgang
    payee: Optional[str] = None
    memo: Optional[str] = None
    category: Optional[str] = None
    number: Optional[str] = None
    cleared: Optional[str] = None
    address: Optional[str] = None
    split_categories: List[SplitCategory] = field(default_factory=list)
    split_memos: List[str] = field(default_factory=list)
    split_amounts: List[str] = field(default_factory=list)
    account: Optional[Account] = None
    qif_class: Optional[QifClass] = None
    category: Optional[Category] = None

    def __post_init__(self):
        self.amount_float: Optional[float] = None
        self.split_amounts_float: List[float] = []
        self.normalize()
        pass

    def normalize(self):
        """
        Normalize the transaction data, converting string amounts to floats.
        """
        try:
            if self.isodate:
                self.isodate = DateUtils.parse_date(self.isodate)
        except Exception as ex:
            self.errors["date"] = ex

        try:
            if self.amount:
                self.amount_float = self.parse_amount(self.amount)
        except Exception as ex:
            self.errors["amount"] = ex

        if self.name:
            if self.memo:
                self.memo = f"{self.name}:{self.memo}"
            else:
                self.memo = self.name

        self.split_amounts_float = []
        for i, amount in enumerate(self.split_amounts):
            try:
                self.split_amounts_float.append(self.parse_amount(amount))
            except Exception as ex:
                self.errors[f"split{i}"].append(ex)

    def parse_amount(self, amount_str: str) -> float:
        # Remove any currency symbols and whitespace
        cleaned_str = re.sub(r"[^\d,.-]", "", amount_str)
        # Replace comma with dot if comma is used as decimal separator
        if "," in cleaned_str and "." not in cleaned_str:
            cleaned_str = cleaned_str.replace(",", ".")
        elif "," in cleaned_str and "." in cleaned_str:
            cleaned_str = cleaned_str.replace(",", "")
        try:
            return float(cleaned_str)
        except ValueError:
            raise ValueError(f"Unable to parse amount: {amount_str}")

    def total_split_amount(self) -> float:
        """
        Calculate the total amount for split transactions.

        Returns:
            float: The sum of all split amounts.
        """
        return sum(self.split_amounts_float)


@lod_storable
class SimpleQifParser:
    """
    a QIF parser
    """

    name: Optional[str] = None
    currency: str = "EUR"
    default_account_type = "EXPENSE"
    options: Dict[str, str] = field(default_factory=dict)
    classes: Dict[str, QifClass] = field(default_factory=dict)
    categories: Dict[str, Category] = field(default_factory=dict)
    accounts: Dict[str, Account] = field(default_factory=dict)
    transactions: Dict[str, Transaction] = field(default_factory=dict)
    accounts: Dict[str, Account] = field(default_factory=dict)
    errors: List[ErrorRecord] = field(default_factory=list)

    def __post_init__(self):
        self.current_account = None
        self.field_names = {
            "$": "split_amount",
            "~": "~?",
            "&": "&?",
            "%": "%?",
            "@": "@?",
            "A": "address",
            "B": "B?",
            "C": "cleared",
            "D": "isodate",
            "E": "split_memo",
            "F": "F?",
            "G": "G?",
            "I": "I?",
            "K": "K?",
            "L": "category",
            "M": "memo",
            "N": "name",
            "O": "O?",
            "R": "R?",
            "P": "payee",
            "Q": "Q?",
            "S": "split_category",
            "T": "amount",
            "U": "amount_unknown",
            "V": "V?",
            "Y": "Y?",
        }

    def parse_file(
        self,
        qif_file: str,
        encoding="iso-8859-1",
        name: str = None,
        verbose: bool = False,
        debug: bool = False,
    ):
        """
        parse a qif file

        Args:
            qif_file (str): Path to the input QIF file.
            encoding (str): File encoding. Defaults to 'iso-8859-1'.
            name (str): name to set if None use the basename of the qif_file
            verbose (bool): if True give verbose output
            debug (bool): if True show debug output
        """
        if name is None:
            name = os.path.basename(qif_file)
        self.name = name
        with open(qif_file, "r", encoding=encoding) as file:
            content = file.readlines()
        self.parse(content, verbose=verbose, debug=debug)

    def parse(self, lines: List[str], verbose: bool = False, debug: bool = False):
        """
        parse the given list of lines
        """
        current_record = {}
        record_type = None
        start_line = 1

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            if debug:
                print(f"{line_num}:{line}")
            if line.startswith("$"):
                self.currency = "USD"
            elif line.startswith("€"):
                self.currency = "EUR"
            if line.startswith("!Option:"):
                option = line[8:]
                self.options[option] = True
            elif line.startswith("!Clear:"):
                option = line[8:]
                self.options[option] = False
            elif line.startswith("!Type:") or line.startswith("!Account"):
                if current_record:
                    self._add_record(
                        record_type, current_record, start_line, line_num - 1
                    )
                if line.startswith("!Account"):
                    record_type = "Account"
                else:
                    record_type = line[6:]  # Text after !Type:
                    pass
                current_record = {}
                start_line = line_num + 1
            elif line == "^":
                if current_record:
                    self._add_record(record_type, current_record, start_line, line_num)
                current_record = {}
                start_line = line_num + 1

            elif line[0] in self.field_names:
                first = line[0]
                key = self.field_names.get(first)
                value = line[1:].strip()
                if key == "name":
                    pass
                if key in ["split_category", "split_memo", "split_amount"]:
                    if key == "split_category":
                        value = SplitCategory(value)
                    if key not in current_record:
                        current_record[key] = []
                    current_record[key].append(value)
                else:
                    current_record[key] = value
            else:
                error = ErrorRecord(start_line=start_line, end_line=line_num, line=line)
                err_msg = f"parser can not handle line {line_num}: {line}"
                if verbose or debug:
                    logging.error(err_msg)
                self.errors.append(error)

        if current_record:
            self._add_record(record_type, current_record, start_line, len(lines))

    def _add_account(
        self,
        account_name: str,
        account_type: str,
        description: str,
        start_line,
        end_line,
    ) -> Account:
        """
        add an account for the given parameters making sure the parent account is created if need be
        """
        parts = account_name.split(":")
        name = parts[-1]
        parent_name = ":".join(parts[:-1]) if len(parts) > 1 else None
        parent_id = parent_name
        if account_type is None:
            account_type = self.default_account_type
        if parent_name and parent_name not in self.accounts:
            self.accounts[parent_name] = Account(
                name=parent_name,
                account_type=account_type,
                currency=self.currency,
                start_line=start_line,
                end_line=end_line,
            )
        account = Account(
            name=name,
            description=description,
            account_type=account_type,
            currency=self.currency,
            parent_account_id=parent_id,
            start_line=start_line,
            end_line=end_line,
        )
        self.accounts[account.name] = account
        return account

    def _add_record(
        self, record_type: str, record: Dict[str, Any], start_line: int, end_line: int
    ):
        """
        add the given record
        """
        record["_start_line"] = start_line
        record["_end_line"] = end_line
        if record_type == "Account":
            # @TODO allow external lookup of currency since quicken does not have it
            # Determine if the account has a parent by checking for a ':' in the name
            account_name = record.get("name", "")
            account_type = account_type = record.get("account_type")
            description = record.get("description", "")
            self.current_account = self._add_account(
                account_name,
                account_type=account_type,
                description=description,
                start_line=start_line,
                end_line=end_line,
            )
        elif record_type == "Class":
            qclass = QifClass(
                name=record.get("name", ""),
                description=record.get("description", ""),
                start_line=start_line,
                end_line=end_line,
            )
            self.classes[qclass.name] = qclass
        elif record_type == "Cat":
            cat = Category(
                name=record.get("name", ""),
                description=record.get("description", ""),
                start_line=start_line,
                end_line=end_line,
            )
            self.categories[cat.name] = cat
        else:
            tx = self.tx_for_record(record)
            if self.current_account:
                tx.account = self.current_account
                account_name = self.current_account.name
                tx_id = f"{account_name}:{tx.isodate}:{tx.start_line}"
            else:
                tx_id = f"{tx.isodate}:{tx.start_line}"

            self.transactions[tx_id] = tx

    def tx_for_record(self, t):
        """
        convert the transaction record
        """
        transaction = Transaction(start_line=t["_start_line"], end_line=t["_end_line"])

        for key, value in t.items():
            if key.startswith("_"):
                continue
            setattr(transaction, key, value)
        transaction.normalize()
        return transaction

    def get_lod(self) -> List[Dict[str, Any]]:
        """
        Get a list of dictionaries representing all transactions.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a transaction.
        """
        lod = []
        for tx in self.transactions.values():
            record = {
                # "tx_id": f"{self.current_account.name}:{tx.isodate}:{tx.start_line}",
                # "account": self.current_account.name,
                "isodate": tx.isodate,
                "amount": tx.amount,
                "payee": tx.payee,
                "memo": tx.memo,
                "category": tx.category,
                "number": tx.number,
                "cleared": tx.cleared,
                "address": tx.address,
                "split_category": (
                    ",".join(tx.split_category) if tx.split_category else None
                ),
                "split_memo": ",".join(tx.split_memo) if tx.split_memo else None,
                "split_amount": (
                    ",".join(map(str, tx.split_amount)) if tx.split_amount else None
                ),
                "qif_class": tx.qif_class.name if tx.qif_class else None,
            }
            lod.append(record)
        return lod

    def print_sample_transactions(self, num_samples: int = 7):
        print(f"\nSample of {min(num_samples, len(self.transactions))} transactions:")
        txs = list(self.transactions.values())[:num_samples]
        for idx, transaction in enumerate(txs, 1):
            print(
                f"Transaction {idx} (lines {transaction.start_line}-{transaction.end_line}):"
            )
            for field, value in vars(transaction).items():
                if field not in ["start_line", "end_line", "errors"]:
                    if isinstance(value, list):
                        print(f"  {field}: {', '.join(map(str, value))}")
                    else:
                        print(f"  {field}: {value}")
            if transaction.errors:
                print("  Errors:")
                for field, error in transaction.errors.items():
                    print(f"    {field}: {type(error).__name__}: {str(error)}")
            print()

    def print_parts(self, parts: dict, title: str, limit: int = 100000):
        print(f"\n{title}:")
        for i, part in enumerate(parts.values(), start=1):
            if i >= limit:
                break
            print(
                f"{i:3}: {part.name} - {part.description} (#{part.start_line}-{part.end_line})"
            )

    def get_stats(self) -> Stats:
        dates = [
            datetime.strptime(tx.isodate, "%Y-%m-%d")
            for tx in self.transactions.values()
            if tx.isodate
        ]
        if dates:
            min_date = min(dates).strftime("%Y-%m-%d")
            max_date = max(dates).strftime("%Y-%m-%d")
        else:
            min_date = max_date = None

        other_stats = {
            "options": self.options,
            "field_histogram": self._get_field_histogram(),
            "error_histogram": self._get_error_histogram(),
        }

        return Stats(
            accounts=len(self.accounts),
            transactions=len(self.transactions),
            start_date=min_date,
            end_date=max_date,
            classes=len(self.classes),
            categories=len(self.categories),
            errors=len(self.errors),
            other=other_stats,
        )

    def _get_field_histogram(self) -> Dict[str, int]:
        field_counter = Counter()
        for transaction in self.transactions.values():
            for field, value in vars(transaction).items():
                if field not in ["start_line", "end_line", "errors"]:
                    if value is not None and (
                        not isinstance(value, list) or len(value) > 0
                    ):
                        field_counter[field] += 1
        return dict(field_counter)

    def _get_error_histogram(self) -> Dict[str, int]:
        error_counter = Counter()
        for transaction in self.transactions.values():
            error_counter.update(transaction.errors.keys())
        return dict(error_counter)

    def generate_error_report(self, max_errors_per_type=10):
        """
        Generate a detailed error report.

        Args:
            max_errors_per_type (int): Maximum number of errors to show for each error type.

        Returns:
            str: A formatted error report.
        """
        error_types = {}
        for transaction in self.transactions.values():
            for field, error in transaction.errors.items():
                error_type = type(error).__name__
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append((transaction, field, error))

        report = ["Detailed Error Report:"]
        for error_type, errors in error_types.items():
            report.append(f"\n{error_type} ({len(errors)} occurrences):")
            for i, (transaction, field, error) in enumerate(
                errors[:max_errors_per_type], 1
            ):
                report.append(
                    f"  {i}. Line {transaction.start_line}-{transaction.end_line}, Field: {field}"
                )
                report.append(f"     Error: {str(error)}")
                report.append(
                    f"     Transaction: {self.transaction_summary(transaction)}"
                )
            if len(errors) > max_errors_per_type:
                report.append(f"  ... and {len(errors) - max_errors_per_type} more.")

        return "\n".join(report)

    def transaction_summary(self, transaction):
        """Helper function to provide a summary of a transaction."""
        summary = []
        for field, value in vars(transaction).items():
            if field not in ["start_line", "end_line", "errors"] and value is not None:
                summary.append(f"{field}: {value}")
        return ", ".join(summary)

    def show_summary(self, limit: int = 7):
        stats = self.get_stats()
        self.stats = stats

        # Display basic statistics
        print(f"Options: {stats.other.get('options', {})}")
        print(f"#classes: {stats.classes}")
        print(f"#categories: {stats.categories}")
        print(f"#accounts: {stats.accounts}")
        print(f"#transactions: {stats.transactions}")
        print(f"#errors: {stats.errors}")
        print(f"Date range: {stats.start_date} to {stats.end_date}")

        # Display field and error histograms
        print("Field histogram:")
        field_histogram = stats.other.get("field_histogram", {})
        for field, count in field_histogram.items():
            print(f"  {field}: {count}")

        print("Error histogram:")
        error_histogram = stats.other.get("error_histogram", {})
        for field, count in error_histogram.items():
            print(f"  {field}: {count}")

        # Display parts
        self.print_parts(self.accounts, "Accounts", limit=limit)
        self.print_parts(self.classes, "Classes", limit=limit)
        self.print_parts(self.categories, "Categories", limit=limit)

        # Display sample transactions
        print("\nSample Transactions:")
        self.print_sample_transactions()

        # Generate and display error report
        error_report = self.generate_error_report()
        print(error_report)
