"""
Created on 2024-10-04

@author: wf
"""

from typing import List

from nomina.ledger import Account, Book, Split, Transaction
from nomina.nomina_converter import BaseToLedgerConverter
from nomina.qif import SimpleQifParser, SplitCategory
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
        self.qif_parser.parse_file(input_path)
        self.set_source(self.qif_parser)
        return self.qif_parser

    def set_source(self, source: SimpleQifParser):
        self.qif_parser = source
        self.source = source

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
        split_category: SplitCategory,
        memo: str,
        negative: bool = False,
    ) -> Split:
        """
        Helper method to add a split for a given split category

        Args:
            qt(QifTransaction): the QIF transaction the split is for
            ledger_book (Book): The ledger book containing accounts.
            amount (float): The amount for the split.
            split_category (str): The split category.
            memo (str): The memo for the split.
            negative(bool): if True the amount should be negated

        Returns:
            Split: The created Split object.

        Raises:
            ValueError: If the target is not found in the ledger book.
        """
        qt_msg = str(qt)
        # determine the account
        if split_category is None:
            return
        else:
            if split_category.account:
                account = ledger_book.lookup_account(split_category.account)
            elif split_category.category:
                # try regular account first
                account = ledger_book.lookup_account(split_category.category)
                # if that does not work fallback to trying lookup the category
                if not account:
                    account_name = f"Category:{split_category.category}"
                    account = ledger_book.lookup_account(account_name)

        if account is None:
            msg = f"invalid split category {split_category} for {qt_msg}"
            self.log.log("⚠️", "split", msg)
            account = ledger_book.lookup_account("Dangling")

        if amount is None:
            self.log.log(f"⚠️", "amount", f"no amount for {qt_msg}")
            amount = 0.0

        if negative:
            amount = -amount

        split = Split(amount=amount, account_id=account.account_id, memo=memo)
        return split

    def calc_splits(self, qt: Transaction, ledger_book: Book) -> List[Split]:
        """
        Create the debit and credit splits for a QIF transaction.

        Args:
            qt (Transaction): The QIF transaction object containing transaction details.
            ledger_book (Book): The ledger book containing accounts.

        Returns:
            List[Split]: A list of splits for the transaction.
        """
        splits = []
        transaction_account = ledger_book.lookup_account(qt.account.name)

        if transaction_account is None:
            qt_msg = str(qt)
            msg = f"unknown account {qt.account.name} in {qt_msg}"
            self.log.log("⚠️", "account", msg)
            return []

        # Handle split transactions
        if qt.split_categories and qt.split_amounts_float:
            total_amount = qt.total_split_amount()

            # Create debit split for the main transaction account
            splits.append(
                Split(
                    amount=total_amount,
                    account_id=transaction_account.account_id,
                    memo=qt.memo,
                )
            )

            # Create credit splits for each split category
            for i in range(len(qt.split_category)):
                split_category = qt.split_category[i]
                split_amount = qt.split_amounts_float[i]
                split_memo = qt.split_memo[i] if i < len(qt.split_memo) else ""

                splits.append(
                    self.add_split(
                        qt,
                        ledger_book=ledger_book,
                        amount=-split_amount,
                        split_category=split_category,
                        memo=split_memo,
                    )
                )
        else:
            # Handle non-split transactions
            debit_split = Split(
                amount=qt.amount_float,
                account_id=transaction_account.account_id,
                memo=qt.memo,
            )
            splits.append(debit_split)
            # credit_split=Split(
            #    amount=-qt.amount_float,
            #    account_id=None,
            #    memo=qt.memo)
            # Create credit split for the category account (source of funds)
            # splits.append(credit_split)
        return splits

    def convert_to_target(self) -> Book:
        """
        Convert the QIF content to a Ledger Book.

        Returns:
            Book: A ledger book containing accounts and transactions.
        """
        # Create a new Book instance
        ledger_book = Book()
        ledger_book.name = self.source.name

        # Create accounts map from QIF data
        self.create_account_lookup(ledger_book)

        # Add transactions to the ledger book
        for transaction_id, qt in self.qif_parser.transactions.items():
            splits = self.calc_splits(qt, ledger_book)

            ledger_transaction = Transaction(
                isodate=qt.isodate,
                description=qt.memo,
                splits=splits,
                payee=qt.payee,
                memo=qt.memo,
            )

            ledger_book.transactions[transaction_id] = ledger_transaction
        self.target = ledger_book
        return ledger_book
