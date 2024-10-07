"""
Created on 2024-10-07

@author: wf
"""
import re
from nomina.date_utils import DateUtils
from nomina.nomina_converter import AccountingFileConverter
from nomina.ledger import Book as LedgerBook, Account as LedgerAccount, Transaction as LedgerTransaction, Split as LedgerSplit
from nomina.beancount import Beancount, Preamble
from beancount.core import data
from typing import Dict, List, Optional
from datetime import datetime
from lodstorage.persistent_log import Log

class BeancountToLedgerConverter(AccountingFileConverter):
    """
    Convert Beancount format to Ledger Book
    """

    def __init__(self, beancount_file: str):
        """
        Constructor
        """
        self.beancount_file = beancount_file
        self.ledger_book = LedgerBook()
        self.account_map: Dict[str, LedgerAccount] = {}
        self.log = Log()

    def convert(self) -> LedgerBook:
        """Convert the Beancount file to a Ledger Book."""
        beancount = Beancount()
        beancount.load_file(self.beancount_file)

        for entry in beancount.entries:
            if isinstance(entry, data.Open):
                self.convert_account(entry)
            elif isinstance(entry, data.Transaction):
                self.convert_transaction(entry)

        return self.ledger_book

    def convert_account(self, entry: data.Open):
        """Create a Ledger account from a Beancount Open directive."""
        account_parts = entry.account.split(':')
        account_type = account_parts[0].upper()
        account_name = ':'.join(account_parts[1:])

        ledger_account = LedgerAccount(
            account_id=entry.account,
            name=account_name,
            account_type=account_type,
            currency=entry.currencies[0] if entry.currencies else "EUR",
            description=entry.meta.get('description', '')
        )
        self.ledger_book.add_account(ledger_account)
        self.account_map[entry.account] = ledger_account

    def convert_transaction(self, entry: data.Transaction):
        """Create a Ledger transaction from a Beancount Transaction."""
        splits = []
        for posting in entry.postings:
            amount = posting.units.number
            account_id = posting.account

            split = LedgerSplit(
                amount=float(amount),
                account_id=account_id,
                memo=posting.meta.get('memo', ''),
                reconciled=False  # Beancount doesn't have a direct equivalent to Ledger's reconciled flag
            )
            splits.append(split)

        ledger_transaction = LedgerTransaction(
            isodate=entry.date.isoformat(),
            description=entry.narration,
            splits=splits,
            payee=entry.payee,
            memo=entry.meta.get('memo', '')
        )

        # Generate a unique ID for the transaction
        transaction_id = f"{ledger_transaction.isodate}:{hash(ledger_transaction.description)}"
        self.ledger_book.transactions[transaction_id] = ledger_transaction


class LedgerToBeancountConverter:
    """
    converter for Ledger Book to Beancount
    """
    def __init__(self, lbook: LedgerBook):
        """
        Initialize the LedgerToBeancountConverter.

        Args:
            lbook (LedgerBook): The ledger book to convert.
        """
        self.lbook = lbook
        self.lbook_stats=lbook.get_stats()
        self.start_date=lbook.get_stats().start_date or DateUtils.iso_date(datetime.now())
        self.beancount = Beancount()
        self.log = Log()

    def convert(self) -> str:
        """
        Convert the ledger book to a Beancount format string with a preamble.

        Returns:
            str: The complete Beancount file content.
        """
        beancount = self.convert_to_beancount()
        stats = self.lbook.get_stats()
        preamble = Preamble(
            start_date=self.start_date,
            end_date=stats.end_date or "Unknown",
            title=self.lbook.name or "Converted Ledger",
            currency=stats.main_currency()
        )
        return beancount.entries_to_string(preamble)

    def convert_to_beancount(self) -> Beancount:
        """
        Convert the ledger book to a Beancount object.

        Returns:
            Beancount: The converted Beancount object.
        """
        for account in self.lbook.accounts.values():
            self.beancount.add_entry(self.convert_account(account))

        for transaction in self.lbook.transactions.values():
            self.beancount.add_entry(self.convert_transaction(transaction))

        return self.beancount

    def get_beancount_name_for_account(self,account:LedgerAccount)->str:
        """
        """
        self.account_type_map = {
            "ROOT": "Equity",
            "BANK": "Assets",
            "EXPENSE": "Expenses",
            "INCOME": "Income",
            "LIABILITY": "Liabilities",
            "EQUITY": "Equity",
            "ASSET": "Assets"
        }
        prefix=self.account_type_map.get(account.account_type,"Assets")
        fq_name=self.lbook.fq_account_name(account)
        if fq_name in self.account_type_map.keys():
            return None
        fq_name = re.sub(r'[ /]', '-', fq_name)
        beancount_account_name=f"{prefix}:{fq_name}"
        return beancount_account_name

    def convert_account(self, account: LedgerAccount) -> Optional[data.Open]:
        """
        Convert a ledger account to a Beancount Open directive.

        Args:
            account (LedgerAccount): The ledger account to convert.

        Returns:
            Optional[data.Open]: The Beancount Open directive, or None if conversion fails.
        """

        currencies = [account.currency] if account.currency else []
        beancount_account_name=self.get_beancount_name_for_account(account)
        if not beancount_account_name:
            return None
        od= self.beancount.create_open_directive(
            fq_account_name=beancount_account_name,
            date=self.start_date,
            currencies=currencies,
            meta={"description": account.description} if account.description else None
        )
        return od

    def convert_transaction(self, transaction: LedgerTransaction) -> Optional[data.Transaction]:
        """
        Convert a ledger transaction to a Beancount Transaction directive.

        Args:
            transaction (Transaction): The ledger transaction to convert.

        Returns:
            Optional[data.Transaction]: The Beancount Transaction directive, or None if conversion fails.
        """
        date = DateUtils.parse_date(transaction.isodate)
        if date is None:
            self.log.log("⚠️", "date_parse", f"Unable to parse date: {transaction.isodate}")
            return None

        postings = []
        for split in transaction.splits:
            split_account = self.lbook.accounts[split.account_id]
            beancount_account_name=self.get_beancount_name_for_account(split_account)
            postings.append((beancount_account_name, split.amount, split_account.currency or "EUR"))

        if not postings:
            self.log.log("⚠️", "transaction_skip", f"Skipping transaction with no valid postings: {transaction.description}")
            return None

        return self.beancount.create_transaction(
            date=date,
            description=transaction.description,
            postings=postings,
            payee=getattr(transaction, 'payee', None),
            metadata={'memo': transaction.memo} if transaction.memo else None
        )