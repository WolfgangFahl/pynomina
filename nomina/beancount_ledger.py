"""
Created on 2024-10-07

@author: wf
"""
from nomina.date_utils import DateUtils
from nomina.nomina_converter import AccountingFileConverter
from nomina.ledger import Book as LedgerBook, Account as LedgerAccount, Transaction as LedgerTransaction, Split as LedgerSplit
from nomina.beancount import Beancount
from beancount.core import data
from typing import Dict, List
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
    def __init__(self, lbook: LedgerBook):
        self.lbook = lbook
        self.beancount = Beancount()
        self.log = Log()

    def convert(self) -> str:
        entries = []

        # Convert accounts
        for account in self.lbook.accounts.values():
            entry = self.convert_account(account)
            if entry:
                entries.append(entry)

        # Convert transactions
        for transaction in self.lbook.transactions.values():
            entry = self.convert_transaction(transaction)
            if entry:
                entries.append(entry)

        if not entries:
            self.log.log("⚠️", "conversion_empty", "No valid entries were generated during conversion")

        return self.beancount.entries_to_string(entries)

    def convert_account(self, account: LedgerAccount) -> data.Open:
        beancount_account = self.get_beancount_account_name(account)
        if beancount_account is None:
            self.log.log("⚠️", "account_convert", f"Unable to convert account: {account.account_id}")
            return None

        currencies = [account.currency] if account.currency else []
        return self.beancount.create_open_directive(
            account=beancount_account,
            date=datetime.now().date(),
            currencies=currencies,
            meta={"description": account.description} if account.description else None
        )

    def convert_transaction(self, transaction: LedgerTransaction) -> data.Transaction:
        parsed_date = DateUtils.parse_date(transaction.isodate)
        if parsed_date is None:
            self.log.log("⚠️", "date_parse", f"Unable to parse date: {transaction.isodate}")
            return None

        date = datetime.strptime(parsed_date, "%Y-%m-%d").date()

        postings = []
        for split in transaction.splits:
            account = self.get_beancount_account_name(self.lbook.accounts[split.account_id])
            if account is None:
                self.log.log("⚠️", "account_convert", f"Unable to convert account: {split.account_id}")
                continue
            postings.append((account, split.amount, "EUR"))  # Assuming EUR as default currency

        if not postings:
            self.log.log("⚠️", "transaction_skip", f"Skipping transaction with no valid postings: {transaction.description}")
            return None

        return self.beancount.create_transaction(
            date=date,
            description=transaction.description,
            postings=postings,
            payee=transaction.payee,
            metadata={'memo': transaction.memo} if transaction.memo else None
        )

    def get_beancount_account_name(self, account: LedgerAccount) -> str:
        """
        Convert a Ledger account name to a Beancount account name.
        """
        type_map = {
            "ASSET": "Assets",
            "LIABILITY": "Liabilities",
            "EQUITY": "Equity",
            "INCOME": "Income",
            "EXPENSE": "Expenses"
        }
        beancount_type = type_map.get(account.account_type, "Unknown")
        if beancount_type == "Unknown":
            self.log.log("⚠️", "account_type", f"Unknown account type: {account.account_type} for account {account.name}")
            return None
        return f"{beancount_type}:{account.name.replace(' ', '-')}"