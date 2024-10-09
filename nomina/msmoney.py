"""
Created on 2024-10-09

@author: wf
"""

import datetime
import os
from json import JSONDecodeError
from zipfile import ZipFile

from lodstorage.yamlable import lod_storable

from nomina.date_utils import DateUtils
from nomina.graph import Graph
from nomina.stats import Stats


@lod_storable
class ZipHeader:
    file_type: str
    version: str
    name: str
    date: str
    size: int
    sha256: str
    jetversion: str


class MsMoney:
    """
    Wrapper for Microsoft Money content
    """

    def __init__(self):
        self.header = None
        self.graph = Graph()

    def load(self, path: str):
        """
        Load Microsoft Money data from a ZIP file or a directory
        """
        if os.path.isdir(path):
            file_generator = self._generate_files_from_directory(path)
        else:
            file_generator = self._generate_files_from_zip(path)

        self._handle_files(file_generator)

    def _generate_files_from_zip(self, zip_path: str):
        """
        Generator that yields file name and file object from a ZIP file
        """
        with ZipFile(zip_path, "r") as zip_file:
            for file_name in zip_file.namelist():
                with zip_file.open(file_name) as file_content:
                    yield file_name, file_content

    def _generate_files_from_directory(self, dir_path: str):
        """
        Generator that yields file name and file object from a directory
        """
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, "r") as file_content:
                yield file_name, file_content

    def _handle_files(self, file_generator):
        """
        Handle the files yielded by the generator (from ZIP or directory)
        """
        for file_name, file_content in file_generator:
            if file_name == "nomina.yaml":
                # Load the YAML file
                self.header = ZipHeader.load_from_yaml_stream(file_content)
            elif file_name.endswith(".json"):
                try:
                    # Load JSON files as networkx nodes
                    self.graph.add_nodes_from_json(file_name, file_content)
                except JSONDecodeError as e:
                    print(f"Error decoding JSON in file {file_name}: {e}")
                    continue

    def get_stats(self) -> Stats:
        """
        Get statistics about the Microsoft Money data.

        Returns:
            Stats: An object containing various statistics about the data.
        """
        graph = self.graph.graph  # Assign for clarity

        # Calculate date range
        dates = []
        for node, data in graph.nodes(data=True):
            if data.get("type") == "TRN" and "date" in data:
                try:
                    date = datetime.datetime.strptime(
                        data["date"].split()[0], "%Y-%m-%d"
                    )
                    dates.append(date)
                except ValueError:
                    print(f"Invalid date format in transaction: {data['date']}")

        if dates:
            min_date = DateUtils.iso_date(min(dates))
            max_date = DateUtils.iso_date(max(dates))
        else:
            min_date = max_date = None

        # Count accounts and calculate currency counts
        accounts = 0
        currency_counts = {}
        for node, data in graph.nodes(data=True):
            if data.get("type") == "ACCT":
                accounts += 1
                currency = data.get("currency", "UNKNOWN")
                currency_counts[currency] = currency_counts.get(currency, 0) + 1

        # Count transactions
        transactions = sum(
            1 for node, data in graph.nodes(data=True) if data.get("type") == "TRN"
        )

        return Stats(
            accounts=accounts,
            transactions=transactions,
            start_date=min_date,
            end_date=max_date,
            currencies=currency_counts,
        )
