"""
Banking ZV Subsembly json export
Created on 2024-10-05

@author: wf
"""

import json
import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from dacite import from_dict
from lodstorage.yamlable import lod_storable
from tabulate import tabulate

from nomina.stats import Stats


@lod_storable
class Transaction:
    """
    Represents a Subsembly/Banking ZV financial transaction with detailed information about the transaction,
    account details, and remittance information.
    """

    # Transaction identifiers
    BtchId: Optional[
        str
    ]  # Batch identifier, e.g., "987654321" will be the same for all splits of a transaction
    Id: str  # Transaction identifier, e.g., "111222333"
    AcctId: str  # Account identifier, e.g., "123456789"

    # Transaction details
    Amt: str  # Transaction amount, e.g., "100.50"
    AmtCcy: str  # Currency of the amount, e.g., "USD"
    BookgDt: str  # Booking date, e.g., "2024-10-09"
    BookgSts: str  # Booking status, e.g., "BOOK"
    CdtDbtInd: str  # Credit/Debit indicator, e.g., "CRDT" for credit
    ValDt: Optional[str]  # Value date, e.g., "2024-10-09"

    # Account owner information
    OwnrAcctBIC: Optional[str]  # BIC, e.g., "ABCDEFGHXXX"
    OwnrAcctBankCode: str  # Bank code, e.g., "12345678"
    OwnrAcctCcy: str  # Account currency, e.g., "USD"
    OwnrAcctIBAN: Optional[str]  # IBAN, e.g., "DE00123456789012345678"
    OwnrAcctNo: str  # Account number, e.g., "1234567890"

    # Remittance information
    RmtdAcctBIC: Optional[str]  # BIC, e.g., "ZYXWVUTSRQP"
    RmtdAcctCtry: Optional[str]  # Country, e.g., "US"
    RmtdAcctIBAN: Optional[str]  # IBAN, e.g., "US00987654321098765432"
    RmtdNm: Optional[str]  # Name, e.g., "Tech Solutions Inc."
    RmtdUltmtNm: Optional[
        str
    ]  # Ultimate name, e.g., "Global Tech Solutions Corporation"

    # Additional transaction information
    BankRef: Optional[str]  # Bank reference number
    BkTxCd: Optional[str]  # Bank transaction code
    BookgTxt: Optional[str]  # Booking text or description
    BtchBookg: Optional[bool]  # Whether part of a batch booking, e.g., False
    Category: Optional[str]  # Transaction category, e.g., "1780 Sales Tax"
    CdtrId: Optional[str]  # Creditor identifier
    Flag: str  # Transaction flag, e.g., "None"
    GVC: Optional[str]  # German 'Geschäftsvorfallcode' (business transaction code)
    Notes: Optional[
        str
    ]  # Additional notes, e.g., "Ref: INV-2024-001 / Training Service EREF: 1234567890 ABWA: Technology Services Ltd"
    PrimaNotaNo: Optional[str]  # Prima nota number
    ReadStatus: bool  # Whether the transaction has been read, e.g., True
    RmtInf: Optional[str]  # Remittance information


@lod_storable
class Account:
    account_id: str
    name: str
    parent_account_id: Optional[str] = None


@lod_storable
class Book:
    """
    a Banking ZV Book
    """

    name: str
    owner: Optional[str] = (None,)
    url: Optional[str] = (None,)
    since: Optional[str] = (None,)
    default_category = "UndefinedCategory"
    account_json_exports: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.accounts: Dict[str, Account] = {}
        self.transactions: List[Transaction] = []
        self.batches: Dict[str, List[Transaction]] = {}

    def organize_batches(self):
        """
        Organize transactions into batches
        """
        self.batches = {}
        for transaction in self.transactions:
            if not transaction.BtchId:
                self.batches[transaction.Id] = [transaction]
            else:
                if transaction.BtchId not in self.batches:
                    self.batches[transaction.BtchId] = []
                self.batches[transaction.BtchId].append(transaction)
        pass

    @classmethod
    def load_from_file(cls, filename: str) -> "Book":
        book = Book.load_from_yaml_file(filename)
        yaml_dir = os.path.dirname(filename)

        # Adjust JSON file paths to be relative to the YAML file
        for account, json_path in book.account_json_exports.items():
            book.account_json_exports[account] = os.path.join(yaml_dir, json_path)

        book.load_accounts_from_accounts_dict(book.account_json_exports)
        return book

    def get_stats(self) -> Stats:
        """
        Calculates and returns statistics related to the transactions, accounts, and other properties of the Book.

        Returns:
            Stats: An object containing various statistics about the Book.
        """
        dates = [
            datetime.strptime(tx.BookgDt, "%Y-%m-%d")
            for tx in self.transactions
            if tx.BookgDt
        ]

        currencies = {}
        categories = set()
        for tx in self.transactions:
            currencies[tx.AmtCcy] = currencies.get(tx.AmtCcy, 0) + 1
            if tx.Category:
                categories.add(tx.Category)

        return Stats(
            accounts=len(self.accounts),
            transactions=len(self.batches),
            start_date=min(dates).strftime("%Y-%m-%d") if dates else None,
            end_date=max(dates).strftime("%Y-%m-%d") if dates else None,
            categories=len(categories),
            currencies=currencies,
            other={"name": self.name, "owner": self.owner},
        )

    def load_accounts_from_accounts_dict(self, account_json_dict: dict):
        """
        Loads transactions from a dictionary of JSON file paths and populates the accounts.

        Args:
            account_json_dict (dict): A dictionary where keys are account IDs and values are paths to JSON files containing transaction data.

        """
        for bank_account, json_file in account_json_dict.items():
            # Load transactions from the JSON file
            txs = self.load_transactions_from_json_file(json_file)
            self.transactions.extend(txs)
            # get the account id from the first transaction
            account_id = txs[0].AcctId

            # Create an account object and add it to the accounts dictionary
            self.accounts[account_id] = Account(
                account_id=account_id, name=bank_account
            )

        # Create category accounts as needed
        self.create_category_accounts()
        self.organize_batches()

    def add_category_account(self, category: str):
        """
        add a category account for the given category
        """
        parts = category.split(":")
        current = ""
        parent = None
        for part in parts:
            if current:
                parent = current
                current += ":"
            current += part
            if current not in self.accounts:
                account = Account(
                    account_id=current, name=part, parent_account_id=parent
                )
                self.accounts[current] = account

    def create_category_accounts(self):
        """
        create the category accounts
        """
        self.add_category_account(self.default_category)
        for transaction in self.transactions:
            category = transaction.Category
            if category:
                self.add_category_account(category)
            else:
                transaction.Category = self.default_category

    @staticmethod
    def load_transactions_from_json_file(json_file_path: str) -> List[Transaction]:
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            trecs = json.load(json_file)
            return [from_dict(Transaction, trec) for trec in trecs]

    def show_batch_histogram(self):
        # Count the occurrence of each batch size
        batch_sizes = [len(batch) for batch in self.batches.values()]
        size_count = Counter(batch_sizes)

        # Prepare data for tabulate
        table_data = [(size, count) for size, count in sorted(size_count.items())]
        headers = ["Batch Size", "Count"]

        # Print the histogram table using tabulate
        print("\nBatch Size Histogram Table:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
