"""
Created on 09.10.2024

@author: wf
"""

from pathlib import Path

from nomina.date_utils import DateUtils
from nomina.ledger import Account, Book, Split, Transaction
from nomina.msmoney import MsMoney
from nomina.nomina_converter import BaseToLedgerConverter


class MicrosoftMoneyToLedgerConverter(BaseToLedgerConverter):
    """
    Microsoft Money to Ledger Converter
    """

    def __init__(self, debug: bool = False):
        """
        Constructor for Microsoft Money to Ledger Book conversion.

        Args:
            debug (bool): Whether to enable debug logging.
        """
        super().__init__(from_format_acronym="MONEY", debug=debug)
        self.ms_money = None

    def load(self, input_path: Path) -> MsMoney:
        """
        Load Microsoft Money data
        """
        self.ms_money = MsMoney()
        self.ms_money.load(str(input_path))
        self.source = self.ms_money
        return self.source

    def convert_to_target(self) -> Book:
        """
        convert the microsoft money entries to a Ledger Book
        """
        book = Book()
        book.name = self.ms_money.header.name if self.ms_money.header else "Unknown"
        book.since = self.ms_money.header.date if self.ms_money.header else None
        graph = self.ms_money.graph.graph
        self.log.log("✅", "graph", f"Total nodes: {len(graph.nodes)}")
        node_types = set(
            data.get("type", "Unknown") for _, data in graph.nodes(data=True)
        )
        self.log.log("✅", "graph", f"Node types: {node_types}")

        # Create accounts
        for node, data in graph.nodes(data=True):
            if data.get("type") == "ACCT":
                account = Account(
                    account_id=str(data.get("hacct")),
                    name=data.get("szFull", ""),
                    account_type=data.get("acct_type", "EXPENSE"),
                    description=data.get("desc", ""),
                    currency=data.get("currency", "EUR"),
                )
                book.add_account(account)

        self.log.log("✅", "accounts", f"Accounts created: {len(book.accounts)}")

        # Create transactions
        for _node, data in graph.nodes(data=True):
            tx_dict = self.ms_money.to_transaction_dict(data)
            if tx_dict is not None:
                isodate = tx_dict["isodate"]
                amount = tx_dict["amount"]
                transaction_id = tx_dict["transaction_id"]
                account_id = tx_dict["account_id"]
                transaction = Transaction(
                    isodate=isodate,
                    description=f"Transaction {transaction_id}",  # No clear description field, using a placeholder
                    splits=[],  # We'll handle splits later
                    payee="",  # No clear payee field in the example
                    memo=f"Amount: {amount}",
                )

                # Add a single split for now, we'll refine this later
                split = Split(
                    amount=float(amount),
                    account_id=account_id,
                    memo=f"Transaction {transaction_id}",
                )
                transaction.splits.append(split)

                book.transactions[transaction_id] = transaction

        self.log.log(
            "✅", "transactions", f"Transactions created: {len(book.transactions)}"
        )

        self.target = book
        return book

    def to_text(self) -> str:
        yaml_str = self.target.to_yaml()
        return yaml_str
