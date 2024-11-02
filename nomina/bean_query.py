"""
Created on 2024-11-02

@author: wf
"""

from beanquery.shell import BQLShell
from beancount.core.inventory import Inventory


class BeanQueryHandler:
    """
    Handles executing named parameterized queries using the BQLShell interface from beanquery.
    """

    def __init__(
        self, beancount_file: str, format: str = "text", numberify: bool = False
    ):
        """
        Initialize the BeanQueryHandler with a Beancount file.

        Args:
            beancount_file (str): Path to the Beancount file.
            format (str): Output format (default: 'text').
            numberify (bool): Whether to remove currencies from the output (default: False).
        """
        self.shell = BQLShell(
            beancount_file,
            None,
            interactive=False,
            runinit=False,
            format=format,
            numberify=numberify,
        )

    def execute_query(
        self,
        query: str,
    ) -> list:
        """
        Execute a beanquery query

        Args:
            query (str): The query to execute.

        Returns:
            list: The query result rows as a list of dicts.
        """
        # Execute the query and return results directly
        cursor = self.shell.context.execute(query)
        rows = cursor.fetchall()
        # Get column names from cursor.description
        column_names = [col.name for col in cursor.description]

        # Construct list of dictionaries for each row
        lod = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                col=column_names[i]
                row_dict[col] = value
                if isinstance(value,Inventory):
                    position = value.get_only_position()
                    if position:
                        amount = position.units.number
                        currency = position.units.currency
                        row_dict[col] = amount
                        row_dict["currency"] = currency
            lod.append(row_dict)

        return lod

