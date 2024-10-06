"""
Created on 04.10.2024

@author: wf
"""

from copy import deepcopy
from dataclasses import field
from datetime import datetime
from typing import Dict, List, Optional
from nomina.stats import Stats
from lodstorage.yamlable import lod_storable


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
    description: str
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
            min_date = min(dates).strftime("%Y-%m-%d")
            max_date = max(dates).strftime("%Y-%m-%d")
        else:
            min_date = max_date = None

        return Stats(
            accounts=len(self.accounts),
            transactions=len(self.transactions),
            start_date=min_date,
            end_date=max_date
        )


    def filter(self, start_date: str = None, end_date: str = None) -> "Book":
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
