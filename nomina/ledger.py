"""
Created on 04.10.2024

@author: wf
"""

from copy import deepcopy
from dataclasses import field
from datetime import datetime
from typing import Dict, List, Optional

from lodstorage.persistent_log import Log
from lodstorage.yamlable import lod_storable

from nomina.date_utils import DateUtils
from nomina.stats import Stats


@lod_storable
class Account:
    """
    Represents a ledger account.
    """

    account_id: str
    name: str
    account_type: str
    description: Optional[str] = ""
    currency: str = "EUR"  # Default to EUR
    parent_account_id: Optional[str] = None


@lod_storable
class Split:
    """
    Represents a split in a transaction.
    """

    amount: float
    account_id: str
    memo: Optional[str] = ""
    reconciled: bool = False


@lod_storable
class Transaction:
    """
    Represents a transaction in the ledger.
    """

    isodate: str
    description: Optional[str] = None
    splits: List[Split] = field(default_factory=list)
    payee: Optional[str] = None
    memo: Optional[str] = ""

    def total_amount(self) -> float:
        """
        Calculates the total amount of the transaction.
        Returns:
            float: The sum of all split amounts.
        """
        return sum(split.amount for split in self.splits)


@lod_storable
class Book:
    """
    Represents a ledger book containing accounts and transactions.
    """

    file_type: str = "NOMINA-LEDGER-BOOK-YAML"
    version: str = "0.1"
    name: Optional[str] = None
    owner: Optional[str] = None
    since: Optional[str] = None
    url: Optional[str] = None
    accounts: Dict[str, Account] = field(default_factory=dict)
    transactions: Dict[str, Transaction] = field(default_factory=dict)

    def __post_init__(self):
        """
        post construct actions
        """
        self.log = Log()

    def fq_account_name(self, account: Account, separator: str = ":") -> str:
        """
        Returns the fully qualified name of the account, using the specified separator.

        Args:
            account (Account): The account for which to generate the fully qualified name.
            separator (str): The separator to use between parent and child account names. Defaults to ':'.

        Returns:
            str: The fully qualified name of the account.
        """
        if account.parent_account_id:
            parent_account = self.lookup_account(account.parent_account_id)
            if parent_account:
                parent_account_name = self.fq_account_name(parent_account, separator)
                return f"{parent_account_name}{separator}{account.name}"
        return account.name

    def get_stats(self) -> Stats:
        """
        Get statistics about the Book.

        Returns:
            Stats: An object containing various statistics about the Book.
        """
        # Calculate date range
        dates = [
            datetime.strptime(tx.isodate.split()[0], "%Y-%m-%d")
            for tx in self.transactions.values()
            if tx.isodate
        ]
        if dates:
            min_date = DateUtils.iso_date(min(dates))
            max_date = DateUtils.iso_date(max(dates))
        else:
            min_date = max_date = None

        # Calculate currency counts
        currency_counts = {}
        for account in self.accounts.values():
            currency = account.currency
            currency_counts[currency] = currency_counts.get(currency, 0) + 1

        return Stats(
            accounts=len(self.accounts),
            transactions=len(self.transactions),
            start_date=min_date,
            end_date=max_date,
            currencies=currency_counts,
        )

    def filter(
        self,
        start_date: str = None,
        end_date: str = None,
        remove_unused_accounts: bool = True,
    ) -> "Book":
        """
        Filter the transactions based on the given date range.

        Args:
            start_date (str): The start date in 'YYYY-MM-DD' format.
            end_date (str): The end date in 'YYYY-MM-DD' format.

        Returns:
            Book: A new Book object with filtered transactions.
        """
        filtered_transactions = {}

        for transaction_id, transaction in self.transactions.items():
            if transaction.isodate is not None:
                transaction_date = transaction.isodate.split()[
                    0
                ]  # Extract 'YYYY-MM-DD' part

                in_range = (not start_date or transaction_date >= start_date) and (
                    not end_date or transaction_date <= end_date
                )

                if in_range:
                    filtered_transactions[transaction_id] = transaction

        filtered_book = deepcopy(self)
        filtered_book.transactions = filtered_transactions
        if remove_unused_accounts:
            filtered_book.remove_unused_accounts()
        return filtered_book

    def create_account(
        self,
        name: str,
        account_type: str = "EXPENSE",
        parent_account_id: Optional[str] = None,
    ) -> Account:
        """
        Create a ledger account with the given parameters.

        Args:
            name (str): The name of the account.
            account_type (str): The type of the account. Defaults to "EXPENSE".
            parent_account_id (Optional[str]): The id of the parent account, if any.

        Returns:
            Account: A new Account object.
        """
        # Calculate the account ID based on the parent's account ID (if any)
        if parent_account_id:
            parent_account = self.lookup_account(parent_account_id)
            if parent_account:
                account_id = f"{parent_account_id}:{name}"
            else:
                raise ValueError(f"invalid parent account {parent_account_id}")
        else:
            account_id = name  # top level account

        # Create the account
        account = Account(
            account_id=account_id,
            name=name,
            account_type=account_type,
            parent_account_id=parent_account_id,
        )
        self.add_account(account)

    def add_account(self, account: Account):
        """
        add the given account
        """
        self.accounts[account.account_id] = account
        return account

    def lookup_account(self, account_id: str) -> Optional[Account]:
        """
        Get the account for the given account id.

        Args:
            account_id(str): The id of the account to look up.

        Returns:
            Optional[Account]: The found account or None if not found.
        """
        return self.accounts.get(account_id)

    def calc_balances(self, lenient: bool = False) -> Dict[str, Optional[float]]:
        """
        Calculate the balances for all accounts, including propagation up the account hierarchy.
        Unused accounts will have a balance of None.

        Returns:
            Dict[str, Optional[float]]: A dictionary mapping account IDs to their balances or None if unused.
        """
        balances = {account_id: None for account_id in self.accounts}

        # First pass: Calculate balances from transactions
        for ti, transaction in enumerate(self.transactions.values(), start=1):
            for si, split in enumerate(transaction.splits, start=1):
                if not split:
                    msg = f"split {si} of transaction {ti} is None"
                    if lenient:
                        self.log.log("⚠️", "split", msg)
                    else:
                        raise ValueError(msg)
                    continue
                else:
                    if balances[split.account_id] is None:
                        balances[split.account_id] = split.amount
                    else:
                        balances[split.account_id] += split.amount

        # Second pass: Propagate balances up the hierarchy
        for account in self.accounts.values():
            if account.parent_account_id:
                child_balance = balances[account.account_id]
                if child_balance is not None:
                    if balances[account.parent_account_id] is None:
                        balances[account.parent_account_id] = child_balance
                    else:
                        balances[account.parent_account_id] += child_balance

        return balances

    def remove_unused_accounts(self) -> None:
        """
        Remove accounts that have not been used in any transactions.
        """
        balances = self.calc_balances()

        # Remove accounts that have not been used (balance is None)
        accounts_to_remove = [
            account_id for account_id, balance in balances.items() if balance is None
        ]
        for account_id in accounts_to_remove:
            del self.accounts[account_id]
