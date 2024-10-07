"""
Created on 2024-10-07

@author: wf
"""
from nomina.date_utils import DateUtils
from nomina.nomina_converter import AccountingFileConverter
from nomina.ledger import Book as LedgerBook, Account as LedgerAccount, Transaction as LedgerTransaction, Split as LedgerSplit
from nomina.beancount import Beancount, Preamble
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
    """
    convert ledger book entries to beancount
    """
    def __init__(self, lbook: LedgerBook):
        self.lbook = lbook
        self.log = Log()

    def convert_to_beancount(self)->Beancount:
        """
        convert to beancount
        """
        beancount=Beancount()

        # Convert accounts
        for account in self.lbook.accounts.values():
            beancount.add_entry(self.convert_account(beancount,account))

        # Convert transactions
        for transaction in self.lbook.transactions.values():
            beancount.add_entry(self.convert_transaction(beancount,transaction))

        return beancount

    def convert(self) -> str:
        """
        Convert the ledger book to a Beancount format string with a preamble.

        Returns:
            str: The complete Beancount file content.
        """
        # Convert the ledger book to Beancount
        beancount = self.convert_to_beancount()

        # Get start and end dates from ledger book statistics
        stats = self.lbook.get_stats()
        start_date = stats.start_date if stats.start_date else "Unknown"
        end_date = stats.end_date if stats.end_date else "Unknown"

        # Create the preamble
        preamble = Preamble(
            start_date=start_date,
            end_date=end_date,
            title=self.lbook.name,
            currency=stats.main_currency()
        )

        # Generate the Beancount file content with the preamble
        return beancount.entries_to_string(preamble)

    def convert_account(self, beancount:Beancount, account: LedgerAccount) -> data.Open:
        currencies = [account.currency] if account.currency else []
        od= beancount.create_open_directive(
            fq_account_name=account.account_id,
            date=datetime.now().date(),
            currencies=currencies,
            meta={"description": account.description} if account.description else None
        )
        return od

    def convert_transaction(self, beancount:Beancount, transaction: LedgerTransaction) -> data.Transaction:
        parsed_date = DateUtils.parse_date(transaction.isodate)
        if parsed_date is None:
            self.log.log("⚠️", "date_parse", f"Unable to parse date: {transaction.isodate}")
            return None

        date = datetime.strptime(parsed_date, "%Y-%m-%d").date()

        postings = []
        for split in transaction.splits:
            split_account=self.lbook.accounts[split.account_id]
            postings.append((split_account.account_id, split.amount, "EUR"))  # Assuming EUR as default currency

        if not postings:
            self.log.log("⚠️", "transaction_skip", f"Skipping transaction with no valid postings: {transaction.description}")
            return None

        return beancount.create_transaction(
            date=date,
            description=transaction.description,
            postings=postings,
            payee=transaction.payee,
            metadata={'memo': transaction.memo} if transaction.memo else None
        )