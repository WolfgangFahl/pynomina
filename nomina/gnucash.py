"""
Created on 2024-10-02

@author: wf
"""

import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.models.datatype import XmlDate

from nomina.date_utils import DateUtils
from nomina.stats import Stats


@dataclass
class VersionedElement:
    version: str = field(
        default="2.0.0",
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class Id:
    class Meta:
        name = "id"
        namespace = "http://www.gnucash.org/XML/act"

    type_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )
    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )


@dataclass
class TsDate:
    date: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/ts",
        },
    )

    def __post_init__(self):
        """
        format date to 1970-01-01 00:00:00 +0000
        """
        if self.date and len(self.date) == 10:
            self.date += " 00:00:00 +0000"


@dataclass
class CountData:
    class Meta:
        name = "count-data"
        namespace = "http://www.gnucash.org/XML/gnc"

    type_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.gnucash.org/XML/cd",
            "required": True,
        },
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "required": True,
        },
    )


@dataclass
class Value:
    class Meta:
        name = "value"
        namespace = "http://www.gnucash.org/XML/slot"

    type_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )
    gdate: Optional[XmlDate] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class Slot:
    key: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/slot",
            "required": True,
        },
    )
    value: Optional[Value] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/slot",
            "required": True,
        },
    )


@dataclass
class Slots:
    class Meta:
        name = "slots"
        namespace = "http://www.gnucash.org/XML/trn"

    slot: Optional[Slot] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class Commodity:
    space: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/cmdty"},
    )
    id: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/cmdty"},
    )
    get_quotes: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/cmdty"},
    )
    quote_source: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/cmdty"},
    )
    quote_tz: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/cmdty"},
    )
    name: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/cmdty"},
    )
    xcode: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/cmdty"},
    )
    fraction: Optional[int] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/cmdty"},
    )


@dataclass
class VersionedCommodity(VersionedElement, Commodity):
    pass


@dataclass
class Split:
    id: Optional[Id] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/split"},
    )
    memo: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/split"},
    )
    reconciled_state: Optional[str] = field(
        default=None,
        metadata={
            "name": "reconciled-state",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/split",
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/split"},
    )
    quantity: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/split"},
    )
    account: Optional[Id] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/split"},
    )


@dataclass
class Transaction(VersionedElement):
    id: Optional[Id] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/trn"},
    )
    currency: Optional[Commodity] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/trn"},
    )
    date_posted: Optional[TsDate] = field(
        default=None,
        metadata={
            "name": "date-posted",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/trn",
        },
    )
    date_entered: Optional[TsDate] = field(
        default=None,
        metadata={
            "name": "date-entered",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/trn",
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/trn"},
    )
    slots: Optional[Slots] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/trn",
            "required": True,
        },
    )
    splits: List[Split] = field(
        default_factory=list,
        metadata={
            "name": "split",
            "wrapper": "splits",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/trn",
        },
    )


@dataclass
class Account(VersionedElement):
    name: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/act"},
    )
    id: Optional[Id] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/act",
            "required": True,
        },
    )
    type: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/act"},
    )
    commodity: Optional[Commodity] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/act",
            "attrs": {"version": None},  # This will remove the version attribute
        },
    )
    commodity_scu: Optional[int] = field(
        default=None,
        metadata={
            "name": "commodity-scu",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/act",
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/act"},
    )
    parent: Optional[Id] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.gnucash.org/XML/act"},
    )


@dataclass
class Book(VersionedElement):
    id: Optional[Id] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/book",
            "required": True,
        },
    )
    count_data: List[CountData] = field(
        default_factory=list,
        metadata={
            "name": "count-data",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/gnc",
        },
    )
    commodities: List[VersionedCommodity] = field(
        default_factory=list,
        metadata={
            "name": "commodity",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/gnc",
        },
    )
    accounts: List[Account] = field(
        default_factory=list,
        metadata={
            "name": "account",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/gnc",
        },
    )
    transactions: List[Transaction] = field(
        default_factory=list,
        metadata={
            "name": "transaction",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/gnc",
        },
    )

    def update_count_data(self):
        # Add count data
        self.count_data = [
            CountData(type_value="account", value=len(self.accounts)),
            CountData(type_value="transaction", value=len(self.transactions)),
            CountData(type_value="commodity", value=1),  # currency only
        ]


@dataclass
class GncV2:
    class Meta:
        name = "gnc-v2"
        namespace = None

    count_data: Optional[CountData] = field(
        default=None,
        metadata={
            "name": "count-data",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/gnc",
            "required": True,
        },
    )
    book: Optional[Book] = field(
        default=None,
        metadata={
            "name": "book",
            "type": "Element",
            "namespace": "http://www.gnucash.org/XML/gnc",
        },
    )

    def get_stats(self) -> Stats:
        """
        Get statistics for the GncV2 object.
        """
        dates = []
        currency_usage = {}

        # Collect dates and currencies from transactions
        for transaction in self.book.transactions:
            if transaction.date_posted and transaction.date_posted.date:
                parsed_date = DateUtils.parse_date(transaction.date_posted.date)
                if parsed_date:
                    dates.append(parsed_date)

            if transaction.currency and transaction.currency.id:
                currency = transaction.currency.id
                if currency in currency_usage:
                    currency_usage[currency] += 1
                else:
                    currency_usage[currency] = 1

        # Determine the date range
        min_date = min(dates) if dates else None
        max_date = max(dates) if dates else None

        return Stats(
            accounts=len(self.book.accounts),
            transactions=len(self.book.transactions),
            start_date=min_date,
            end_date=max_date,
            currencies=currency_usage,
        )


class GnuCashXml:
    """
    GnuCash XML reader/writer
    """

    def __init__(self, indent: str = "  "):
        """
        constructor
        using two space indentation
        """
        self.indent = indent
        self.namespaces = {
            "gnc": "http://www.gnucash.org/XML/gnc",
            "act": "http://www.gnucash.org/XML/act",
            "book": "http://www.gnucash.org/XML/book",
            "cd": "http://www.gnucash.org/XML/cd",
            "cmdty": "http://www.gnucash.org/XML/cmdty",
            "price": "http://www.gnucash.org/XML/price",
            "slot": "http://www.gnucash.org/XML/slot",
            "split": "http://www.gnucash.org/XML/split",
            "sx": "http://www.gnucash.org/XML/sx",
            "trn": "http://www.gnucash.org/XML/trn",
            "ts": "http://www.gnucash.org/XML/ts",
            "fs": "http://www.gnucash.org/XML/fs",
            "bgt": "http://www.gnucash.org/XML/bgt",
            "recurrence": "http://www.gnucash.org/XML/recurrence",
            "lot": "http://www.gnucash.org/XML/lot",
            "addr": "http://www.gnucash.org/XML/addr",
            "billterm": "http://www.gnucash.org/XML/billterm",
            "bt-days": "http://www.gnucash.org/XML/bt-days",
            "bt-prox": "http://www.gnucash.org/XML/bt-prox",
            "cust": "http://www.gnucash.org/XML/cust",
            "employee": "http://www.gnucash.org/XML/employee",
            "entry": "http://www.gnucash.org/XML/entry",
            "invoice": "http://www.gnucash.org/XML/invoice",
            "job": "http://www.gnucash.org/XML/job",
            "order": "http://www.gnucash.org/XML/order",
            "owner": "http://www.gnucash.org/XML/owner",
            "taxtable": "http://www.gnucash.org/XML/taxtable",
            "tte": "http://www.gnucash.org/XML/tte",
            "vendor": "http://www.gnucash.org/XML/vendor",
        }

    def parse_gnucash_xml(self, xml_file: str) -> GncV2:
        """
        parse the given gnucash xml file
        """
        parser = XmlParser(config=ParserConfig(fail_on_unknown_properties=False))
        return parser.parse(xml_file, GncV2)

    def xml_format(self, xml_string: str) -> str:
        """
        adapt the format of the xml_string to gnu cash conventions
        """
        # unindent two spaces twice
        formatted_xml = re.sub(r"(\n  )", r"\n", xml_string)
        formatted_xml = re.sub(r"(\n  )", r"\n", formatted_xml)

        # formatting of xmlns attributes
        xmlns_indent = "     "  # Five spaces
        formatted_xml = re.sub(
            r'\s(xmlns:[^=]+="[^"]+")', f"\n{xmlns_indent}\\1", formatted_xml
        )

        # Ensure there's a space before the closing ?> in the XML declaration
        formatted_xml = formatted_xml.replace("?>", " ?>")

        # Consistent empty element formatting
        formatted_xml = re.sub(r"<([^>]+)\/>", r"<\1/>", formatted_xml)

        # add a new line at end
        formatted_xml += "\n"

        return formatted_xml

    def to_text(self, gnucash_data: GncV2) -> str:
        """
        Serialize the GnuCash data object to an XML string.

        Args:
            gnucash_data (GncV2): The GnuCash data object to serialize.

        Returns:
            str: The serialized XML string.
        """
        serializer = XmlSerializer(
            config=SerializerConfig(
                xml_declaration=True,
                encoding="utf-8",
                indent=self.indent,
            )
        )

        with io.StringIO() as xml_buffer:
            serializer.write(xml_buffer, gnucash_data, ns_map=self.namespaces)
            xml_string = xml_buffer.getvalue()

        # Apply the custom filter to the XML string
        formatted_xml_string = self.xml_format(xml_string)

        return formatted_xml_string

    def write_gnucash_xml(self, gnucash_data: GncV2, output_file: str) -> None:
        """
        Serialize the GnuCash data object to an XML file.

        Args:
            gnucash_data (GnuCashXml): The GnuCash data object to serialize.
            output_file (str): The file path where the XML will be written.
        """
        xml_string = self.to_text(gnucash_data)

        # Write the formatted XML string to the file
        with open(output_file, "w", encoding="UTF-8") as f:
            f.write(xml_string)
