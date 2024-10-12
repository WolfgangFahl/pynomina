"""
Created on 2024-10-06

@author: wf
"""

from dataclasses import field
from typing import Any, Dict, Optional

from lodstorage.yamlable import lod_storable


@lod_storable
class Stats:
    """
    Ledger statistics
    """

    accounts: int
    transactions: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    classes: Optional[int] = None
    categories: Optional[int] = None
    errors: Optional[int] = None
    currencies: Dict[str, int] = field(default_factory=dict)
    other: Optional[Dict[str, Any]] = field(default_factory=dict)

    def show(self):
        print(f"# Accounts: {self.accounts}")
        print(f"# Transactions: {self.transactions}")
        print(f"Date Range: {self.start_date} to {self.end_date}")

        if self.classes is not None:
            print(f"# Classes: {self.classes}")

        if self.categories is not None:
            print(f"# Categories: {self.categories}")

        if self.errors is not None:
            print(f"# Errors: {self.errors}")

        if self.currencies:
            print(
                f"# Currencies: {', '.join(f'{currency}: {count}' for currency, count in self.currencies.items())}"
            )

        if self.other:
            print("Other Details:")
            for key, value in self.other.items():
                print(f"  {key}: {value}")

    def main_currency(self) -> Optional[str]:
        """
        Determine the main currency used in the ledger.

        Returns:
            Optional[str]: The currency with the highest count, or None if no currencies are present.
        """
        if not self.currencies:
            return None
        return max(self.currencies, key=self.currencies.get)
