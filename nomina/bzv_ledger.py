"""
Created on 2024-10-05

@author: wf
"""

from typing import List, TextIO

from nomina.bzv import Account
from nomina.bzv import Book as BzvBook
from nomina.bzv import Transaction as BzvTransaction
from nomina.file_formats import AccountingFileFormats
from nomina.ledger import Account as LedgerAccount
from nomina.ledger import Book as LedgerBook
from nomina.ledger import Split as LedgerSplit
from nomina.ledger import Transaction as LedgerTransaction
from nomina.nomina_converter import AccountingFileConverter


class BankingZVToLedgerConverter(AccountingFileConverter):
    """
    convert BankingZV Entries to Leder format
    """

    def __init__(self, debug: bool = False):
        """
        Constructor for BankingZV to Ledger Book conversion.

        Args:
            bzv_book (BzvBook): The BankingZV book object to be converted.
            debug (bool): Whether to enable debug logging.
        """
        formats = AccountingFileFormats()
        from_format = formats.get_by_acronym("BZV-JSON")
        to_format = formats.get_by_acronym("LB-YAML")

        # Call the superclass constructor with the looked-up formats
        super().__init__(from_format, to_format, debug)

    def load(self, input_stream: TextIO):
        self.bzv_book = BzvBook.load_from_file(input_stream)
        self.source = self.bzv_book
        return self.source

    def create_ledger_account(self, bzv_account: Account) -> LedgerAccount:
        """
        create a ledger account from a banking ZV account
        """
        account = LedgerAccount(
            account_id=bzv_account.account_id,
            name=bzv_account.name,
            account_type="BANK" if ":" not in bzv_account.account_id else "CATEGORY",
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

        return splits

    def create_ledger_transaction(
        self, transaction: BzvTransaction
    ) -> LedgerTransaction:
        return LedgerTransaction(
            isodate=transaction.BookgDt,
            description=transaction.BookgTxt or "No description",
            splits=self.create_ledger_splits(transaction),
            memo=transaction.RmtInf or "",
        )

    def convert_to_target(self) -> LedgerBook:
        ledger_book = LedgerBook(
            owner=self.bzv_book.owner, url=self.bzv_book.url, name=self.bzv_book.name
        )

        for bzv_account in self.bzv_book.accounts.values():
            ledger_account = self.create_ledger_account(bzv_account)
            ledger_book.accounts[ledger_account.account_id] = ledger_account

        for transaction in self.bzv_book.transactions:
            ledger_transaction = self.create_ledger_transaction(transaction)
            transaction_id = f"{ledger_transaction.isodate}:{transaction.Id}"
            ledger_book.transactions[transaction_id] = ledger_transaction
        self.target = ledger_book
        return ledger_book

    def to_text(self) -> str:
        yaml_str = self.target.to_yaml()
        return yaml_str
