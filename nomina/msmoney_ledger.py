"""
Created on 09.10.2024

@author: wf
"""

from pathlib import Path

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
        graph=self.ms_money.graph.graph
        self.log.log("✅", "graph", f"Total nodes: {len(graph.nodes)}")
        node_types = set(
            data.get("type", "Unknown")
            for _, data in graph.nodes(data=True)
        )
        self.log.log("✅", "graph", f"Node types: {node_types}")

        # Create accounts
        for node, data in graph.nodes(data=True):
            if data.get("type") == "ACCT":
                account = Account(
                    account_id=node,
                    name=data.get("name", ""),
                    account_type=data.get("acct_type", "EXPENSE"),
                    description=data.get("desc", ""),
                    currency=data.get("currency", "EUR"),
                )
                book.add_account(account)

        self.log.log("✅", "accounts", f"Accounts created: {len(book.accounts)}")

        # Create transactions
        for node, data in graph.nodes(data=True):
            if data.get("type") == "TRN":
                splits = []
                for split_node in graph.neighbors(node):
                    split_data = graph.nodes[split_node]
                    if split_data.get("type") == "TRN_SPLIT":
                        split = Split(
                            amount=float(split_data.get("amount", 0)),
                            account_id=split_data.get("account_id", ""),
                            memo=split_data.get("memo", ""),
                        )
                        splits.append(split)

                if not splits:
                    self.log.log(
                        "⚠️", "transaction", f"No splits found for transaction {node}"
                    )

                transaction = Transaction(
                    isodate=data.get("date", ""),
                    description=data.get("desc", ""),
                    splits=splits,
                    payee=data.get("payee", ""),
                )
                book.transactions[node] = transaction

        self.log.log(
            "✅", "transactions", f"Transactions created: {len(book.transactions)}"
        )

        self.target = book
        return book

    def to_text(self) -> str:
        yaml_str = self.target.to_yaml()
        return yaml_str
