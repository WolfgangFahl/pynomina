"""
Banking ZV Subsembly json export
Created on 2024-10-05

@author: wf
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from dacite import from_dict
from lodstorage.yamlable import lod_storable

from nomina.stats import Stats


@lod_storable
class Transaction:
    Id: str
    AcctId: str
    OwnrAcctCcy: str
    OwnrAcctIBAN: Optional[str]
    OwnrAcctNo: str
    OwnrAcctBIC: Optional[str]
    OwnrAcctBankCode: str
    BookgDt: str
    ValDt: Optional[str]
    Amt: str
    AmtCcy: str
    CdtDbtInd: str
    CdtrId: Optional[str]
    RmtInf: Optional[str]
    BookgTxt: Optional[str]
    PrimaNotaNo: Optional[str]
    BankRef: Optional[str]
    BkTxCd: Optional[str]
    BookgSts: str
    GVC: Optional[str]
    Category: Optional[str]
    ReadStatus: bool
    Flag: str


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
    account_json_exports: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.accounts: Dict[str, Account] = {}
        self.transactions: List[Transaction] = []

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
            transactions=len(self.transactions),
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
        for transaction in self.transactions:
            category = transaction.Category
            if category:
                self.add_category_account(category)

    @staticmethod
    def load_transactions_from_json_file(json_file_path: str) -> List[Transaction]:
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            trecs = json.load(json_file)
            return [from_dict(Transaction, trec) for trec in trecs]
