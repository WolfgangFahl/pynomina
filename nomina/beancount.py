"""
Created on 2024-10-07

@author: wf
"""
import io
from beancount.parser import printer
from beancount import loader
from beancount.core import data, amount
from typing import List, Dict, Optional, Tuple
from datetime import date
from nomina.stats import Stats

class Beancount:
    """
    Encapsulates Beancount-specific operations and conversions
    """

    def __init__(self):
        self.entries: List[data.Directive] = []
        self.errors: List[str] = []
        self.options_map: Dict = {}

    def load_file(self, file_path: str) -> None:
        """
        Load a Beancount file

        Args:
            file_path (str): Path to the Beancount file
        """
        self.entries, self.errors, self.options_map = loader.load_file(file_path)

    def load_string(self, beancount_string: str) -> None:
        """
        Load Beancount data from a string

        Args:
            beancount_string (str): Beancount data as a string
        """
        self.entries, self.errors, self.options_map = loader.load_string(beancount_string)

    def create_open_directive(self, account: str, date: date, currencies: Optional[List[str]] = None, meta: Optional[Dict] = None) -> data.Open:
        """
        Create a Beancount Open directive

        Args:
            account (str): Account name
            date (date): Opening date
            currencies (Optional[List[str]]): List of currencies for the account
            meta (Optional[Dict]): Metadata for the Open directive

        Returns:
            data.Open: Beancount Open directive
        """
        return data.Open(meta or {}, date, account, currencies or [], None)

    def create_transaction(self, date: date, description: str, postings: List[Tuple[str, float, str]],
                           payee: str = None, metadata: Dict = None) -> data.Transaction:
        """
        Create a Beancount Transaction directive

        Args:
            date (date): Transaction date
            description (str): Transaction description
            postings (List[Tuple[str, float, str]]): List of (account, amount, currency) tuples
            payee (str, optional): Payee name
            metadata (Dict, optional): Transaction metadata

        Returns:
            data.Transaction: Beancount Transaction directive
        """
        meta = data.new_metadata("", 0, metadata)
        txn_postings = []
        for account, amount_value, currency in postings:
            amt = amount.Amount(amount.D(str(amount_value)), currency)
            txn_postings.append(data.Posting(account, amt, None, None, None, None))

        return data.Transaction(meta, date, '*', payee, description, data.EMPTY_SET, data.EMPTY_SET, txn_postings)

    def entries_to_string(self, entries: Optional[List[data.Directive]] = None) -> str:
        entries_to_print = entries if entries is not None else self.entries
        output = io.StringIO()
        printer.print_entries(entries_to_print, file=output)
        return output.getvalue()

    def get_stats(self) -> Stats:
        """
        Get statistics about the Beancount data

        Returns:
            Stats: An object containing various statistics about the Beancount data
        """
        accounts = set()
        transactions = 0
        dates = []

        for entry in self.entries:
            if isinstance(entry, data.Open):
                accounts.add(entry.account)
            elif isinstance(entry, data.Transaction):
                transactions += 1
                dates.append(entry.date)

        start_date = min(dates).isoformat() if dates else None
        end_date = max(dates).isoformat() if dates else None

        return Stats(
            accounts=len(accounts),
            transactions=transactions,
            start_date=start_date,
            end_date=end_date,
            errors=len(self.errors),
            other={
                "commodities": len(set(entry.currency for entry in self.entries if isinstance(entry, data.Commodity))),
            }
        )