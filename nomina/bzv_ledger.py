"""
Created on 2024-10-05

@author: wf
"""

import re
from pathlib import Path
from typing import List

from nomina.bzv import Account
from nomina.bzv import Book as BzvBook
from nomina.bzv import Transaction as BzvTransaction
from nomina.ledger import Account as LedgerAccount
from nomina.ledger import Book as LedgerBook
from nomina.ledger import Split as LedgerSplit
from nomina.ledger import Transaction as LedgerTransaction
from nomina.nomina_converter import BaseToLedgerConverter


class BankingZVToLedgerConverter(BaseToLedgerConverter):
    """
    convert BankingZV Entries to Ledger format
    """

    def __init__(self, debug: bool = False):
        """
        Constructor for BankingZV to Ledger Book conversion.

        Args:
            debug (bool): Whether to enable debug logging.
        """
        super().__init__(from_format_acronym="BZV-YAML", debug=debug)

    def load(self, input_path: Path) -> BzvBook:
        """
        load the book
        """
        bzv_book = BzvBook.load_from_file(input_path)
        self.set_source(bzv_book)
        return bzv_book

    def set_source(self, bzv_book: BzvBook):
        self.bzv_book = bzv_book
        self.source = self.bzv_book
        return self.source

    def map_account_type(self, bzv_account: Account) -> str:
        """
        get the account type
        """
        account_type = "CATEGORY"
        if bzv_account.parent_account_id is None:
            # name is a pure number
            if re.fullmatch(r"\d+", bzv_account.name):
                account_type = "BANK"
        return account_type

    def create_ledger_account(self, bzv_account: Account) -> LedgerAccount:
        """
        create a ledger account from a banking ZV account
        """
        account_type = self.map_account_type(bzv_account)
        account = LedgerAccount(
            account_id=bzv_account.account_id,
            name=bzv_account.name,
            account_type=account_type,
            description=f"",
            currency="EUR",
            parent_account_id=bzv_account.parent_account_id,
        )
        return account

    def create_ledger_splits(self, transaction: BzvTransaction) -> List[LedgerSplit]:
        """
        create the ledger split
        """
        amount = float(transaction.Amt)
        # CRDT or DBIT?
        if transaction.CdtDbtInd == "DBIT":
            amount = -amount

        splits = [
            LedgerSplit(
                amount=amount,
                account_id=transaction.AcctId,
                memo=transaction.RmtInf or "",
            )
        ]

        if transaction.Category:
            splits.append(
                LedgerSplit(
                    amount=-amount,
                    account_id=transaction.Category,
                    memo=transaction.RmtInf or "",
                )
            )
        else:
            pass

        return splits

    def create_batch_transaction(
        self, batch_id: str, batch_transactions: List[BzvTransaction]
    ) -> LedgerTransaction:
        """
        Create a single ledger transaction for a batch of BZV transactions
        """
        is_split = len(batch_transactions) > 1 and batch_id is not None
        first_tx = batch_transactions[0]
        memo = f"{batch_id}"
        if is_split:
            description = first_tx.Notes
            payee = first_tx.RmtdNm
        else:
            description = first_tx.RmtInf
            payee = first_tx.RmtdNm
            delim = "->"
            if first_tx.BookgTxt:
                memo += f"{delim}{first_tx.BookgTxt}"
            if first_tx.CdtrId:
                memo += f"{delim}{first_tx.CdtrId}"
        splits = []
        for tx in batch_transactions:
            splits.extend(self.create_ledger_splits(tx))

        lt = LedgerTransaction(
            isodate=first_tx.BookgDt,
            payee=payee,
            description=description,
            splits=splits,
            memo=memo,
        )
        return lt

    def convert_to_target(self) -> LedgerBook:
        """
        convert my Banking ZV book to a ledger book
        """
        ledger_book = LedgerBook(
            owner=self.bzv_book.owner, url=self.bzv_book.url, name=self.bzv_book.name
        )

        for bzv_account in self.bzv_book.accounts.values():
            ledger_account = self.create_ledger_account(bzv_account)
            ledger_book.accounts[ledger_account.account_id] = ledger_account

        # Process all batches (including single-transaction "batches")
        for batch_id, batch_transactions in self.bzv_book.batches.items():
            ledger_transaction = self.create_batch_transaction(
                batch_id, batch_transactions
            )
            transaction_id = f"{ledger_transaction.isodate}:{batch_id}"
            ledger_book.transactions[transaction_id] = ledger_transaction

        self.target = ledger_book
        return ledger_book

    def to_text(self) -> str:
        yaml_str = self.target.to_yaml()
        return yaml_str
