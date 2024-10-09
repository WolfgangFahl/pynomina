"""
Created on 2024-10-04

@author: wf
"""

import uuid
from typing import Dict

from nomina.gnucash import (
    Account,
    Book,
    Commodity,
    CountData,
    GncV2,
    GnuCashXml,
    Id,
    Slot,
    Slots,
    Split,
    Transaction,
    TsDate,
    Value,
)
from nomina.ledger import Account as LedgerAccount
from nomina.ledger import Book as LedgerBook
from nomina.ledger import Split as LedgerSplit
from nomina.ledger import Transaction as LedgerTransaction
from nomina.nomina_converter import BaseFromLedgerConverter, BaseToLedgerConverter


class GnuCashToLedgerConverter(BaseToLedgerConverter):
    """
    Convert GnuCash Book to Ledger Book
    """

    def __init__(self, debug: bool = False):
        """
        constructor
        """
        super().__init__(from_format_acronym="GC-XML", debug=debug)
        self.gnc_v2 = None
        self.account_map: Dict[str, LedgerAccount] = {}
        self.gcxml = GnuCashXml()

    def load(self, input_path: str) -> GncV2:
        """
        Load the GnuCash XML file from the input file and parse it into a GncV2 object.

        Args:
            input_path (str): The input path to read the GnuCash XML data from.

        Returns:
            GncV2: The parsed GncV2 object.
        """
        self.gnc_v2 = self.gcxml.parse_gnucash_xml(input_path)
        return self.gnc_v2

    def create_ledger_account(self, gnc_account: Account) -> LedgerAccount:
        """Create a Ledger account from a GnuCash account."""
        account_id = gnc_account.id.value
        parent_account_id = gnc_account.parent.value if gnc_account.parent else None

        ledger_account = LedgerAccount(
            account_id=account_id,
            name=gnc_account.name,
            account_type=gnc_account.type,
            description=gnc_account.description or "",
            currency=gnc_account.commodity.id if gnc_account.commodity else "EUR",
            parent_account_id=parent_account_id,
        )
        self.account_map[gnc_account.id.value] = ledger_account
        return ledger_account

    def create_ledger_split(self, gnc_split: Split) -> LedgerSplit:
        """Create a Ledger split from a GnuCash split."""
        amount = (
            float(gnc_split.value.split("/")[0]) / 100
        )  # Convert from cents to float
        return LedgerSplit(
            amount=amount,
            account_id=gnc_split.account.value,
            memo=gnc_split.memo or "",
            reconciled=gnc_split.reconciled_state == "y",
        )

    def create_ledger_transaction(
        self, gnc_transaction: Transaction
    ) -> LedgerTransaction:
        """Create a Ledger transaction from a GnuCash transaction."""
        ledger_splits = [
            self.create_ledger_split(split) for split in gnc_transaction.splits
        ]
        return LedgerTransaction(
            isodate=gnc_transaction.date_posted.date,
            description=gnc_transaction.description,
            splits=ledger_splits,
            memo=gnc_transaction.description,
        )

    def convert_to_target(self) -> LedgerBook:
        """Convert the GnuCash V2 structure to a Ledger Book."""
        ledger_book = LedgerBook()

        # Convert accounts
        for gnc_account in self.gnc_v2.book.accounts:
            ledger_account = self.create_ledger_account(gnc_account)
            ledger_book.accounts[ledger_account.account_id] = ledger_account

        # Convert transactions
        for gnc_transaction in self.gnc_v2.book.transactions:
            ledger_transaction = self.create_ledger_transaction(gnc_transaction)
            # Using a simple transaction ID for demonstration
            transaction_id = (
                f"{ledger_transaction.isodate}:{ledger_transaction.description}"
            )
            ledger_book.transactions[transaction_id] = ledger_transaction

        return ledger_book

    def to_text(self) -> str:
        """
        create the output text
        """
        yaml_str = self.target.to_yaml()
        return yaml_str


class LedgerToGnuCashConverter(BaseFromLedgerConverter):
    """
    Convert Ledger Book to GnuCash Book
    """

    def __init__(self, debug: bool = False):
        """
        Constructor for Ledger Book to GnuCash conversion.

        Args:
            debug (bool): Whether to enable debug logging.
        """
        super().__init__(to_format_acronym="GC-XML", debug=debug)

        # Initialize instance variables
        self.lbook = None
        self.account_map = {}
        self.gcxml = GnuCashXml()

    def load(self, input_path: str) -> LedgerBook:
        """
        load the Ledger Book

        Returns:
            LedgerBook: the ledger book
        """
        lbook = LedgerBook.load_from_yaml_file(input_path)
        self.set_source(lbook)
        return lbook

    def set_source(self, source: LedgerBook):
        self.source = source
        self.lbook = source

    def generate_guid(self) -> str:
        """Generate a GUID for GnuCash entities."""
        return uuid.uuid4().hex

    def create_gnucash_account(self, laccount: LedgerAccount) -> Account:
        """Create a GnuCash account from a Ledger account."""
        gnc_account = Account(
            name=laccount.name,
            id=Id(type_value="guid", value=self.generate_guid()),
            type=laccount.account_type,
            commodity=Commodity(space="CURRENCY", id=laccount.currency),
            commodity_scu=100,
            parent=(
                Id(
                    type_value="guid",
                    value=self.account_map[laccount.parent_account_id].id.value,
                )
                if laccount.parent_account_id
                else None
            ),
            description=laccount.description,
            version="2.0.0",
        )
        self.account_map[laccount.account_id] = gnc_account
        return gnc_account

    def create_gnucash_split(
        self, lsplit: LedgerSplit, transaction_currency: str
    ) -> Split:
        """Create a GnuCash split from a Ledger split."""
        split = None
        if lsplit and lsplit.amount:
            if lsplit.account_id in self.account_map:
                account_id = self.account_map[lsplit.account_id].id.value
                split = Split(
                    id=Id(type_value="guid", value=self.generate_guid()),
                    memo=lsplit.memo,
                    reconciled_state="n",
                    value=f"{int(lsplit.amount * 100)}/100",
                    quantity=f"{int(lsplit.amount * 100)}/100",
                    account=Id(type_value="guid", value=account_id),
                )
            else:
                self.log.log(
                    "❌", "split", f"unknown split account {lsplit.account_id}"
                )
        return split

    def create_gnucash_transaction(
        self, ltransaction: LedgerTransaction
    ) -> Transaction:
        """Create a GnuCash transaction from a Ledger transaction."""
        currency = Commodity(space="CURRENCY", id="EUR")  # Assuming EUR as default
        gnc_splits = []
        for lsplit in ltransaction.splits:
            split = self.create_gnucash_split(lsplit, currency.id)
            if split:
                gnc_splits.append(split)

        return Transaction(
            id=Id(type_value="guid", value=self.generate_guid()),
            currency=currency,
            date_posted=TsDate(date=ltransaction.isodate),
            date_entered=TsDate(date=ltransaction.isodate),
            description=ltransaction.description,
            splits=gnc_splits,
            slots=Slots(
                slot=Slot(
                    key="date-posted",
                    value=Value(type_value="gdate", gdate=ltransaction.isodate),
                )
            ),
            version="2.0.0",
        )

    def convert_to_target(self) -> GncV2:
        """Convert the Ledger Book to a GnuCash V2 structure."""
        self.account_map: Dict[str, Account] = {}

        # Create GnuCash accounts
        gnc_accounts = [
            self.create_gnucash_account(account)
            for account in self.lbook.accounts.values()
        ]

        # Create GnuCash transactions
        gnc_transactions = [
            self.create_gnucash_transaction(transaction)
            for transaction in self.lbook.transactions.values()
        ]

        # Create GnuCash Book
        book = Book(
            id=Id(type_value="guid", value=self.generate_guid()),
            commodities=[
                Commodity(space="CURRENCY", id="EUR")
            ],  # Assuming EUR as default
            accounts=gnc_accounts,
            transactions=gnc_transactions,
            version="2.0.0",
        )
        book.update_count_data()

        # Create GncV2
        gnc_v2 = GncV2(count_data=CountData(type_value="book", value=1), book=book)
        self.target = gnc_v2
        return gnc_v2

    def to_text(self) -> str:
        """
        convert to text
        """
        xml_string = self.gcxml.to_text(self.target)
        return xml_string
