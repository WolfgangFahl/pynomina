"""
Created on 2024-10-04

@author: wf
"""

from typing import List

from nomina.file_formats import AccountingFileFormats
from nomina.ledger import Account, Book, Split, Transaction
from nomina.nomina_converter import BaseFromLedgerConverter, BaseToLedgerConverter
from nomina.qif import SimpleQifParser
from nomina.qif import Transaction as QifTransaction


class QifToLedgerConverter(BaseToLedgerConverter):
    """
    Convert Quicken QIF file to a Ledger Book.
    """

    def __init__(self, debug: bool = False):
        """
        Constructor for QIF to Ledger Book conversion.

        Args:
            debug (bool): Whether to enable debug logging.
        """
        super().__init__(from_format_acronym="QIF", debug=debug)
        self.qif_parser = SimpleQifParser()

    def load(self, input_path: str):
        """
        Load the content from the input stream.
        """
        with open(input_path, "r") as input_stream:
            self.qif_content = input_stream.read()
        self.qif_lines = self.qif_content.splitlines()
        self.qif_parser.parse(self.qif_lines)
        self.source = self.qif_parser
        return self.qif_parser

    def to_text(self) -> str:
        """
        Convert the target Ledger Book to YAML text.
        """
        return self.target.to_yaml()

    def create_account_lookup(self, ledger_book: Book):
        """
        Create a lookup of account names to Account objects from the QIF data.

        Args:
            ledger_book (Book): The ledger book to populate with accounts to use
            for lookup
        """
        # Create root accounts for classes and categories
        ledger_book.create_account("Class", account_type="CLASS")
        ledger_book.create_account("Category", account_type="CATEGORY")
        ledger_book.create_account("Dangling", account_type="ERROR")

        # Create accounts from QIF data
        for account_name, account_data in self.qif_parser.accounts.items():
            parent_account_id = account_data.parent_account_id
            ledger_book.create_account(
                name=account_name,
                account_type=account_data.account_type,
                parent_account_id=parent_account_id,
            )

        # Create accounts for classes
        for class_name, _class_data in self.qif_parser.classes.items():
            ledger_book.create_account(
                name=class_name, account_type="CLASS", parent_account_id="Class"
            )

        # Create accounts for categories
        for category_name, _category_data in self.qif_parser.categories.items():
            ledger_book.create_account(
                name=category_name,
                account_type="CATEGORY",
                parent_account_id="Category",
            )

    def add_split(
        self,
        qt: QifTransaction,
        ledger_book: Book,
        amount: float,
        target: str,
        memo: str,
        negative: bool = False,
    ) -> Split:
        """
        Helper method to add a split for a given target (category or account).

        Args:
            qt(QifTransaction): the QIF transaction the split is for
            ledger_book (Book): The ledger book containing accounts.
            amount (float): The amount for the split.
            target (str): The target name (category or account).
            memo (str): The memo for the split.
            negative(bool): if True the amount should be negated

        Returns:
            Split: The created Split object.

        Raises:
            ValueError: If the target is not found in the ledger book.
        """
        qt_msg = str(qt)
        if target is None:
            msg = f"empty split target for {qt_msg}"
            self.log.log("⚠️", "split", msg)
            return
        target_name = target.strip(
            "[]"
        )  # Remove brackets if present -> target is account
        if target.startswith("["):
            account = ledger_book.lookup_account(target_name)
        else:
            # try regular account first
            account = ledger_book.lookup_account(target_name)
            # if that does not work fallback to trying lookup the category
            if not account:
                target_name = f"Category:{target_name}"
                account = ledger_book.lookup_account(target_name)

        if account is None:
            msg = f"invalid split target {target} for {qt_msg}"
            self.log.log("⚠️", "split", msg)
            account = ledger_book.lookup_account("Dangling")

        if amount is None:
            self.log.log(f"⚠️", "amount", f"no amount for {qt_msg}")
            amount = 0.0

        if negative:
            amount = -amount

        split = Split(amount=amount, account_id=account.account_id, memo=memo)
        return split

    def calc_splits(
        self, transaction_data: Transaction, ledger_book: Book
    ) -> List[Split]:
        """
        Create the debit and credit splits for a QIF transaction.

        Args:
            transaction_data (Transaction): The QIF transaction object containing transaction details.
            ledger_book (Book): The ledger book containing accounts.

        Returns:
            List[Split]: A list of splits for the transaction.
        """
        splits = []
        transaction_account = ledger_book.lookup_account(transaction_data.account.name)

        if transaction_account is None:
            qt_msg = str(transaction_data)
            msg = f"unknown account in {qt_msg}"
            self.log.log("⚠️", "account", msg)
            return []

        # Handle split transactions
        if transaction_data.split_category and transaction_data.split_amounts_float:
            total_amount = transaction_data.total_split_amount()

            # Create debit split for the main transaction account
            splits.append(
                Split(
                    amount=total_amount,
                    account_id=transaction_account.account_id,
                    memo=transaction_data.memo,
                )
            )

            # Create credit splits for each split category
            for i in range(len(transaction_data.split_category)):
                split_target = transaction_data.split_category[i]
                split_amount = transaction_data.split_amounts_float[i]
                split_memo = (
                    transaction_data.split_memo[i]
                    if i < len(transaction_data.split_memo)
                    else ""
                )

                splits.append(
                    self.add_split(
                        transaction_data,
                        ledger_book=ledger_book,
                        amount=-split_amount,
                        target=split_target,
                        memo=split_memo,
                    )
                )
        else:
            # Handle non-split transactions
            splits.append(
                Split(
                    amount=transaction_data.amount_float,
                    account_id=transaction_account.account_id,
                    memo=transaction_data.memo,
                )
            )

            # Create credit split for the category account (source of funds)
            splits.append(
                self.add_split(
                    transaction_data,
                    ledger_book=ledger_book,
                    amount=transaction_data.amount_float,
                    target=transaction_data.category,
                    memo=transaction_data.memo,
                    negative=True,
                )
            )

        return splits

    def convert_to_target(self) -> Book:
        """
        Convert the QIF content to a Ledger Book.

        Returns:
            Book: A ledger book containing accounts and transactions.
        """
        # Create a new Book instance
        ledger_book = Book()

        # Create accounts map from QIF data
        self.create_account_lookup(ledger_book)

        # Add transactions to the ledger book
        for transaction_id, transaction_data in self.qif_parser.transactions.items():
            splits = self.calc_splits(transaction_data, ledger_book)

            ledger_transaction = Transaction(
                isodate=transaction_data.isodate,
                description=transaction_data.memo,
                splits=splits,
                payee=transaction_data.payee,
                memo=transaction_data.memo,
            )

            ledger_book.transactions[transaction_id] = ledger_transaction
        self.target = ledger_book
        return ledger_book
